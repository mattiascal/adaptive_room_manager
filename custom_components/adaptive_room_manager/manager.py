"""Event-driven room controller."""
from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_XY_COLOR,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    EVENT_HOMEASSISTANT_STARTED,
    STATE_CLOSED,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import CoreState, HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    AREA_OFF_EXCLUDE_LABEL,
    CONF_ABSENCE_DELAY,
    CONF_AREA_ID,
    CONF_COVERS,
    CONF_DAY_LIGHTS,
    CONF_ENTRY_TYPE,
    CONF_EVENING_LIGHTS,
    CONF_EVENING_START,
    CONF_LUX,
    CONF_LUX_THRESHOLD,
    CONF_MORNING_START,
    CONF_NIGHT_LIGHTS,
    CONF_NIGHT_START,
    CONF_PERSISTENT,
    CONF_SLEEP_ABSENCE_DELAY,
    CONF_SLEEP_AUTO_OFF,
    CONF_SLEEP_BRIGHTNESS,
    CONF_SLEEP_COLOR_MODE,
    CONF_SLEEP_COLOR_TEMP,
    CONF_SLEEP_LIGHT_ON,
    CONF_SLEEP_LIGHT_PROFILES,
    CONF_SLEEP_LIGHTS,
    CONF_SLEEP_RESTORE_TRANSITION,
    CONF_SLEEP_RGB_COLOR,
    CONF_SLEEP_TRANSITION,
    CONF_TRIGGER_PRESENCE,
    CONF_SYNC_ENTER_DAY,
    CONF_SYNC_ENTER_EVENING,
    CONF_SYNC_ENTER_NIGHT,
    DEFAULT_ABSENCE_DELAY,
    DEFAULT_EVENING_START,
    DEFAULT_LUX_THRESHOLD,
    DEFAULT_MORNING_START,
    DEFAULT_NIGHT_START,
    DEFAULT_SLEEP_ABSENCE_DELAY,
    DEFAULT_SLEEP_AUTO_OFF,
    DEFAULT_SLEEP_RESTORE_TRANSITION,
    DEFAULT_SLEEP_TRANSITION,
    DEFAULT_SYNC_ENTER_DAY,
    DEFAULT_SYNC_ENTER_EVENING,
    DEFAULT_SYNC_ENTER_NIGHT,
    DOMAIN,
    ENTRY_TYPE_HOME,
    LUX_SETTLE_SECONDS,
    SLEEP_COLOR_RGB,
    SLEEP_COLOR_TEMP,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)


class RoomManager:
    """Calculate presence and control lighting for one area."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.listeners: list = []
        self.callbacks: list = []
        self.occupied = False
        self.light_needed = False
        self.presence_reason = "No active presence sensors"
        self.light_reason = "Not evaluated"
        self.sleep_reason = "Sleep mode inactive"
        self.enabled = True
        self.mode = "automatic"
        self.last_natural_lux: float | None = None
        self.auto_lights: set[str] = set()
        # Area lights switched on during the cycle by anyone other than ARM's
        # profile (by hand, app, other automations). Switched off only on vacancy.
        self.turned_on_lights: set[str] = set()
        self._area_light_ids: set[str] = set()
        self.manual_overrides: set[str] = set()
        self.sleep_mode = False
        self._sleep_snapshot: dict[str, dict[str, Any]] = {}
        self._last_light_states: dict[str, dict[str, Any]] = {}
        self._storage_save_cancel = None
        self._startup_restore_cancel = None
        self._startup_completed = False
        self._restoring_lights = False
        self._absence_cancel = None
        # Natural lux is not sampled right after a light went off: the sensor
        # still reports the artificial light for a few seconds.
        self._lux_settle_until = 0.0
        self._lux_settle_cancel = None
        # Delayed switch-off of tracked lights that came back on (after being
        # unavailable) while the room is vacant.
        self._orphan_sweep_cancel = None
        self._sleep_profile_applied = False
        # A normal Day/Evening/Night profile is applied at most once during an
        # occupancy cycle. This prevents a light switched off by the user from
        # being turned back on by later sensor/lux/state evaluations.
        self._lighting_profile_applied = False
        self._last_period: str | None = None
        self._store = Store[dict[str, Any]](
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}.{entry.entry_id}"
        )

    @property
    def config(self) -> dict:
        return {**self.entry.data, **self.entry.options}

    @property
    def home_config(self) -> dict:
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HOME:
                return {**entry.data, **entry.options}
        return {}

    @property
    def area_id(self) -> str:
        return self.entry.data[CONF_AREA_ID]

    @property
    def room_name(self) -> str:
        area = ar.async_get(self.hass).async_get_area(self.area_id)
        return area.name if area else self.entry.title

    @property
    def absence_delay(self) -> int:
        return int(self.config.get(CONF_ABSENCE_DELAY, DEFAULT_ABSENCE_DELAY))

    @property
    def sleep_absence_delay_minutes(self) -> int:
        return int(
            self.config.get(CONF_SLEEP_ABSENCE_DELAY, DEFAULT_SLEEP_ABSENCE_DELAY)
        )

    @property
    def current_absence_delay(self) -> int:
        if self.sleep_mode:
            return self.sleep_absence_delay_minutes * 60
        return self.absence_delay

    @property
    def sleep_auto_off(self) -> bool:
        return bool(self.config.get(CONF_SLEEP_AUTO_OFF, DEFAULT_SLEEP_AUTO_OFF))

    @property
    def lux_threshold(self) -> float:
        return float(self.config.get(CONF_LUX_THRESHOLD, DEFAULT_LUX_THRESHOLD))

    @property
    def entities(self) -> list[str]:
        out: list[str] = []
        for key in (
            CONF_TRIGGER_PRESENCE,
            CONF_PERSISTENT,
            CONF_LUX,
            CONF_COVERS,
            CONF_DAY_LIGHTS,
            CONF_EVENING_LIGHTS,
            CONF_NIGHT_LIGHTS,
            CONF_SLEEP_LIGHTS,
        ):
            out.extend(self.config.get(key, []))
        out.append("sun.sun")
        return list(dict.fromkeys(out))

    async def async_start(self) -> None:
        stored = await self._store.async_load() or {}
        self._sleep_snapshot = stored.get("snapshot", {})
        self.sleep_mode = bool(stored.get("sleep_mode", False))
        self._last_light_states = stored.get("light_states", {})
        # Lights ARM is responsible for switching off on vacancy. Persisted so a
        # Home Assistant restart does not orphan lights that are still on.
        self.auto_lights = set(stored.get("auto_lights", [])) & self._all_lights()
        self.turned_on_lights = set(stored.get("turned_on_lights", []))

        # During a full Home Assistant startup, wait until all integrations have
        # restored their entities before replaying the last known room-light state.
        # On an integration reload Home Assistant is already running, so a short
        # delay is sufficient and avoids fighting the light platforms' own restore.
        if self.hass.state == CoreState.running:
            self._schedule_startup_restore(1)
        else:
            self.listeners.append(
                self.hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STARTED, self._home_assistant_started
                )
            )

    @callback
    def _home_assistant_started(self, _event) -> None:
        self._schedule_startup_restore(3)

    @callback
    def _schedule_startup_restore(self, delay: float) -> None:
        if self._startup_restore_cancel is not None:
            self._startup_restore_cancel()
        self._startup_restore_cancel = async_call_later(
            self.hass, delay, self._finish_startup
        )

    @callback
    def _finish_startup(self, _now) -> None:
        self._startup_restore_cancel = None
        self.hass.async_create_task(self._async_finish_startup())

    async def _async_finish_startup(self) -> None:
        if self._startup_completed:
            return
        await self._restore_last_light_states()

        # If the room is already occupied after a restart, consider the current
        # profile handled so a restored manual light state is not immediately
        # replaced by the active Day/Evening/Night or Sleep profile.
        triggers, persistent = self._active_presence()
        occupied_now = bool(triggers and persistent)
        self._lighting_profile_applied = occupied_now
        self._sleep_profile_applied = occupied_now and self.sleep_mode

        # The absence timer does not survive a restart. If lights of the Area are
        # still on, resume the occupancy cycle so the normal absence delay runs
        # again and switches them off once the room is confirmed empty.
        # A light that is still unavailable/unknown this early (slow integrations
        # such as Zigbee2MQTT) is kept: only lights known to be off are dropped,
        # so a light that comes back on later is still switched off.
        self.auto_lights = {
            entity_id
            for entity_id in self.auto_lights
            if not self._light_is_off(entity_id)
        }
        area_lights = self._area_lights()
        self._area_light_ids = area_lights
        self.turned_on_lights = {
            entity_id
            for entity_id in self.turned_on_lights & area_lights
            if not self._light_is_off(entity_id)
        }
        tracked_on = {
            entity_id
            for entity_id in self.auto_lights | self.turned_on_lights
            if self._light_is_on(entity_id)
        }
        if tracked_on and not self.sleep_mode:
            self.occupied = True
            self._lighting_profile_applied = True

        self.listeners.append(
            async_track_state_change_event(self.hass, self.entities, self._state_changed)
        )
        tracked = sorted(area_lights - set(self.entities))
        if tracked:
            self.listeners.append(
                async_track_state_change_event(
                    self.hass, tracked, self._area_light_changed
                )
            )
        self._schedule_period_boundaries()
        self._last_period = self.period()
        self._startup_completed = True
        await self.async_evaluate()

    async def async_stop(self) -> None:
        self._capture_all_light_states()
        await self._save_persistent_state()
        for remove_listener in self.listeners:
            remove_listener()
        self.listeners.clear()
        self._cancel_absence_timer()
        if self._lux_settle_cancel is not None:
            self._lux_settle_cancel()
            self._lux_settle_cancel = None
        if self._orphan_sweep_cancel is not None:
            self._orphan_sweep_cancel()
            self._orphan_sweep_cancel = None
        if self._storage_save_cancel is not None:
            self._storage_save_cancel()
            self._storage_save_cancel = None
        if self._startup_restore_cancel is not None:
            self._startup_restore_cancel()
            self._startup_restore_cancel = None

    def add_callback(self, callback_func) -> None:
        self.callbacks.append(callback_func)

    def remove_callback(self, callback_func) -> None:
        if callback_func in self.callbacks:
            self.callbacks.remove(callback_func)

    @callback
    def _state_changed(self, event) -> None:
        entity_id = event.data.get("entity_id")
        if entity_id in self._area_light_ids or entity_id in self.auto_lights:
            self._track_turned_on(event)
        if entity_id in self._all_lights() or entity_id in self._area_light_ids:
            self._hold_natural_lux_if_switched_off(event)
        if entity_id in self._all_lights() and not self._restoring_lights:
            self._capture_light_state(entity_id)
            self._schedule_persistent_state_save()
        self.hass.async_create_task(self.async_evaluate(entity_id))

    @callback
    def _period_boundary(self, _now) -> None:
        """Re-evaluate the room exactly when a configured period begins."""
        self.hass.async_create_task(self.async_evaluate(period_boundary=True))

    def _schedule_period_boundaries(self) -> None:
        """Register exact daily callbacks for Day, Evening and Night starts."""
        home = self.home_config
        for key, default in (
            (CONF_MORNING_START, DEFAULT_MORNING_START),
            (CONF_EVENING_START, DEFAULT_EVENING_START),
            (CONF_NIGHT_START, DEFAULT_NIGHT_START),
        ):
            boundary = time.fromisoformat(home.get(key, default))
            self.listeners.append(
                async_track_time_change(
                    self.hass,
                    self._period_boundary,
                    hour=boundary.hour,
                    minute=boundary.minute,
                    second=boundary.second,
                )
            )

    def _is_active(self, entity_id: str) -> bool:
        state = self.hass.states.get(entity_id)
        return state is not None and state.state.lower() not in (
            "off", "closed", STATE_UNAVAILABLE, STATE_UNKNOWN,
            "idle", "standby", "none", "0",
        )

    def _active_presence(self) -> tuple[list[str], list[str]]:
        triggers = [
            entity_id
            for entity_id in self.config.get(CONF_TRIGGER_PRESENCE, [])
            if self._is_active(entity_id)
        ]
        persistent = [
            entity_id
            for entity_id in self.config.get(CONF_PERSISTENT, [])
            if self._is_active(entity_id)
        ]
        return triggers, persistent

    def _all_lights(self) -> set[str]:
        return set(
            self.config.get(CONF_DAY_LIGHTS, [])
            + self.config.get(CONF_EVENING_LIGHTS, [])
            + self.config.get(CONF_NIGHT_LIGHTS, [])
            + self.config.get(CONF_SLEEP_LIGHTS, [])
        )

    def _area_lights(self) -> set[str]:
        """Return the room-lighting entities of the room's Area.

        An entity belongs to the Area through its own area or, when it has none,
        through its device. Light groups, config/diagnostic entities (sensor and
        camera LEDs) and lights labelled ``arm_exclude`` are left out.
        """
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)
        out: set[str] = set()
        for entry in ent_reg.entities.values():
            if entry.domain != "light" or entry.disabled_by is not None:
                continue
            if entry.entity_category is not None:
                continue
            if AREA_OFF_EXCLUDE_LABEL in entry.labels:
                continue
            area_id = entry.area_id
            if area_id is None and entry.device_id:
                device = dev_reg.async_get(entry.device_id)
                area_id = device.area_id if device else None
            if area_id != self.area_id:
                continue
            state = self.hass.states.get(entry.entity_id)
            if state is not None and state.attributes.get(ATTR_ENTITY_ID):
                continue
            out.add(entry.entity_id)
        return out

    def _light_is_on(self, entity_id: str) -> bool:
        state = self.hass.states.get(entity_id)
        return state is not None and state.state == STATE_ON

    def _light_is_off(self, entity_id: str) -> bool:
        state = self.hass.states.get(entity_id)
        return state is not None and state.state == STATE_OFF

    def _light_is_lost(self, entity_id: str) -> bool:
        """Return whether a light cannot currently receive a command."""
        state = self.hass.states.get(entity_id)
        return state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)

    @callback
    def _track_turned_on(self, event) -> None:
        """Remember an Area light switched on, forget it once it is off."""
        entity_id = event.data.get("entity_id")
        old = event.data.get("old_state")
        new = event.data.get("new_state")
        if new is None:
            return
        if new.state == STATE_OFF:
            if entity_id in self.turned_on_lights:
                self.turned_on_lights.discard(entity_id)
                self._schedule_persistent_state_save()
            return
        if new.state != STATE_ON or (old is not None and old.state == STATE_ON):
            return
        # A light that reappears already on (it was unavailable or unknown, for
        # example while Home Assistant or its integration restarted) is tracked
        # like one that was switched on.
        returned = old is None or old.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)
        if (
            entity_id in self._area_light_ids
            and entity_id not in self.auto_lights
            and entity_id not in self.turned_on_lights
        ):
            self.turned_on_lights.add(entity_id)
            self._schedule_persistent_state_save()
        if returned:
            self._schedule_orphan_sweep()

    @callback
    def _schedule_orphan_sweep(self) -> None:
        """Switch off returned lights after the absence delay if the room is vacant.

        Outside an occupancy cycle no vacancy event will ever fire, so a tracked
        light that comes back on in an empty room would stay on until the next
        presence. Sleep mode is left alone: its lights are meant to stay on.
        """
        if not self._startup_completed or self.occupied or self.sleep_mode:
            return
        if self._orphan_sweep_cancel is not None:
            self._orphan_sweep_cancel()
        self._orphan_sweep_cancel = async_call_later(
            self.hass, self.absence_delay, self._orphan_sweep
        )

    @callback
    def _orphan_sweep(self, _now) -> None:
        self._orphan_sweep_cancel = None
        if (
            self.occupied
            or self.sleep_mode
            or not self.enabled
            or self.mode == "disabled"
        ):
            return
        tracked = self.auto_lights | self.turned_on_lights
        to_off = {entity_id for entity_id in tracked if self._light_is_on(entity_id)}
        if not to_off:
            return
        self.auto_lights.difference_update(to_off)
        self.turned_on_lights.difference_update(to_off)
        self._schedule_persistent_state_save()
        self.hass.async_create_task(
            self.hass.services.async_call(
                "light", "turn_off", {ATTR_ENTITY_ID: list(to_off)}, blocking=False
            )
        )

    @callback
    def _hold_natural_lux_if_switched_off(self, event) -> None:
        """Pause natural-lux sampling for a moment after a light went off."""
        old = event.data.get("old_state")
        new = event.data.get("new_state")
        if old is None or new is None:
            return
        if old.state != STATE_ON or new.state != STATE_OFF:
            return
        self._lux_settle_until = self.hass.loop.time() + LUX_SETTLE_SECONDS
        if self._lux_settle_cancel is not None:
            self._lux_settle_cancel()
        self._lux_settle_cancel = async_call_later(
            self.hass, LUX_SETTLE_SECONDS + 1, self._lux_settled
        )

    @callback
    def _lux_settled(self, _now) -> None:
        self._lux_settle_cancel = None
        self.hass.async_create_task(self.async_evaluate())

    @callback
    def _area_light_changed(self, event) -> None:
        """Area light not configured in any profile: only track it."""
        self._track_turned_on(event)
        self._hold_natural_lux_if_switched_off(event)

    def _lights_on(self) -> set[str]:
        return {
            entity_id
            for entity_id in self._all_lights()
            if (state := self.hass.states.get(entity_id)) and state.state == STATE_ON
        }

    def period(self) -> str:
        if self.mode.startswith("force_"):
            return self.mode.removeprefix("force_")
        now = dt_util.now().time()
        home = self.home_config
        morning = time.fromisoformat(home.get(CONF_MORNING_START, DEFAULT_MORNING_START))
        evening = time.fromisoformat(home.get(CONF_EVENING_START, DEFAULT_EVENING_START))
        night = time.fromisoformat(home.get(CONF_NIGHT_START, DEFAULT_NIGHT_START))
        if now >= night or now < morning:
            return "night"
        if now >= evening:
            return "evening"
        return "day"

    def _cancel_absence_timer(self) -> None:
        if self._absence_cancel:
            self._absence_cancel()
            self._absence_cancel = None

    async def _save_persistent_state(self) -> None:
        await self._store.async_save(
            {
                "sleep_mode": self.sleep_mode,
                "snapshot": self._sleep_snapshot,
                "light_states": self._last_light_states,
                "auto_lights": sorted(self.auto_lights),
                "turned_on_lights": sorted(self.turned_on_lights),
            }
        )

    async def _save_sleep_state(self) -> None:
        await self._save_persistent_state()

    @callback
    def _schedule_persistent_state_save(self) -> None:
        if self._storage_save_cancel is not None:
            self._storage_save_cancel()
        self._storage_save_cancel = async_call_later(
            self.hass, 1, self._flush_persistent_state
        )

    @callback
    def _flush_persistent_state(self, _now) -> None:
        self._storage_save_cancel = None
        self.hass.async_create_task(self._save_persistent_state())

    def _capture_light_state(self, entity_id: str) -> None:
        saved = self._capture_one_light(entity_id)
        if saved is None or saved.get("state") in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        self._last_light_states[entity_id] = saved

    def _capture_all_light_states(self) -> None:
        for entity_id in self._all_lights():
            self._capture_light_state(entity_id)

    def _saved_light_matches_current(
        self, entity_id: str, saved: dict[str, Any]
    ) -> bool:
        current = self.hass.states.get(entity_id)
        if current is None or current.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return False
        if current.state != saved.get("state"):
            return False
        if current.state != STATE_ON:
            return True
        attrs = current.attributes
        for attribute in (
            ATTR_BRIGHTNESS,
            ATTR_RGB_COLOR,
            ATTR_XY_COLOR,
            ATTR_HS_COLOR,
            ATTR_COLOR_TEMP_KELVIN,
        ):
            saved_value = saved.get(attribute)
            if saved_value is not None and attrs.get(attribute) != saved_value:
                return False
        return True

    async def _restore_last_light_states(self) -> None:
        if not self._last_light_states:
            self._capture_all_light_states()
            await self._save_persistent_state()
            return

        self._restoring_lights = True
        try:
            for entity_id in self._all_lights():
                saved = self._last_light_states.get(entity_id)
                if not saved or self._saved_light_matches_current(entity_id, saved):
                    continue
                current = self.hass.states.get(entity_id)
                if current is None or current.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                    continue
                if saved.get("state") != STATE_ON:
                    await self.hass.services.async_call(
                        "light",
                        "turn_off",
                        {ATTR_ENTITY_ID: entity_id},
                        blocking=True,
                    )
                    continue

                data: dict[str, Any] = {ATTR_ENTITY_ID: entity_id}
                if saved.get(ATTR_BRIGHTNESS) is not None:
                    data[ATTR_BRIGHTNESS] = saved[ATTR_BRIGHTNESS]
                color_mode = saved.get(ATTR_COLOR_MODE)
                if saved.get(ATTR_RGB_COLOR) is not None and color_mode == "rgb":
                    data[ATTR_RGB_COLOR] = saved[ATTR_RGB_COLOR]
                elif saved.get(ATTR_XY_COLOR) is not None and color_mode == "xy":
                    data[ATTR_XY_COLOR] = saved[ATTR_XY_COLOR]
                elif saved.get(ATTR_HS_COLOR) is not None and color_mode == "hs":
                    data[ATTR_HS_COLOR] = saved[ATTR_HS_COLOR]
                elif saved.get(ATTR_COLOR_TEMP_KELVIN) is not None:
                    data[ATTR_COLOR_TEMP_KELVIN] = saved[ATTR_COLOR_TEMP_KELVIN]
                await self.hass.services.async_call(
                    "light", "turn_on", data, blocking=True
                )
        finally:
            self._restoring_lights = False

    def _capture_one_light(self, entity_id: str) -> dict[str, Any] | None:
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        attrs = state.attributes
        return {
            "state": state.state,
            ATTR_BRIGHTNESS: attrs.get(ATTR_BRIGHTNESS),
            ATTR_COLOR_MODE: attrs.get(ATTR_COLOR_MODE),
            ATTR_RGB_COLOR: attrs.get(ATTR_RGB_COLOR),
            ATTR_XY_COLOR: attrs.get(ATTR_XY_COLOR),
            ATTR_HS_COLOR: attrs.get(ATTR_HS_COLOR),
            ATTR_COLOR_TEMP_KELVIN: attrs.get(ATTR_COLOR_TEMP_KELVIN),
        }

    def _sleep_target_requires_command(self, entity_id: str) -> bool:
        """Return whether applying Sleep mode would change this light."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return False

        profiles = self.config.get(CONF_SLEEP_LIGHT_PROFILES, {})
        sleep_lights = set(self.config.get(CONF_SLEEP_LIGHTS, []))
        profile = profiles.get(entity_id, {})
        target_on = entity_id in sleep_lights and profile.get(
            CONF_SLEEP_LIGHT_ON, True
        )

        if not target_on:
            return state.state == STATE_ON
        if state.state != STATE_ON:
            return True

        brightness_pct = profile.get(CONF_SLEEP_BRIGHTNESS)
        if brightness_pct is not None:
            current_brightness = state.attributes.get(ATTR_BRIGHTNESS)
            target_brightness = round(int(brightness_pct) * 255 / 100)
            if current_brightness is None or abs(current_brightness - target_brightness) > 2:
                return True

        color_mode = profile.get(CONF_SLEEP_COLOR_MODE)
        if color_mode == SLEEP_COLOR_RGB and profile.get(CONF_SLEEP_RGB_COLOR):
            current_rgb = state.attributes.get(ATTR_RGB_COLOR)
            if tuple(current_rgb or ()) != tuple(profile[CONF_SLEEP_RGB_COLOR]):
                return True
        elif color_mode == SLEEP_COLOR_TEMP and profile.get(CONF_SLEEP_COLOR_TEMP):
            current_kelvin = state.attributes.get(ATTR_COLOR_TEMP_KELVIN)
            if current_kelvin != int(profile[CONF_SLEEP_COLOR_TEMP]):
                return True

        return False

    def _lights_changed_by_sleep_profile(self) -> set[str]:
        """Return only lights whose state or attributes Sleep mode changes."""
        return {
            entity_id
            for entity_id in self._all_lights()
            if self._sleep_target_requires_command(entity_id)
        }

    def _capture_sleep_snapshot(self) -> dict[str, dict[str, Any]]:
        snapshot: dict[str, dict[str, Any]] = {}
        for entity_id in self._lights_changed_by_sleep_profile():
            saved = self._capture_one_light(entity_id)
            if saved is not None:
                snapshot[entity_id] = saved
        return snapshot

    async def async_set_sleep_mode(self, enabled: bool) -> None:
        if enabled == self.sleep_mode:
            return
        self._cancel_absence_timer()
        if enabled:
            await self._enter_sleep_mode()
        else:
            await self._exit_sleep_mode()
        await self.async_evaluate()

    async def _enter_sleep_mode(self) -> None:
        self.sleep_mode = True
        # Snapshot only entities that will actually receive a sleep-mode command.
        self._sleep_snapshot = self._capture_sleep_snapshot()
        self.sleep_reason = "Enabled by the room Sleep mode switch"
        await self._save_sleep_state()
        await self._apply_sleep_profile()
        self._sleep_profile_applied = True

    async def _exit_sleep_mode(self) -> None:
        self.sleep_mode = False
        self.sleep_reason = "Sleep mode inactive"
        self._sleep_profile_applied = False
        self._update_presence(schedule_timer=False)

        triggers, persistent = self._active_presence()
        if self.occupied and not (triggers or persistent):
            # The room was only being held by the (long) sleep absence delay.
            # With no sensor active it is empty: end the occupancy cycle now
            # instead of restoring lights for nobody.
            self.occupied = False
            self.presence_reason = "Sleep ended with no active presence sensors"
            self._lighting_profile_applied = False
            self.manual_overrides.clear()

        self._update_light_need()

        if self.occupied and self.light_needed:
            await self._restore_light_snapshot()
            # Whatever stays on after Sleep mode belongs to this occupancy cycle
            # and is switched off on vacancy, also when Sleep mode itself (or a
            # restart during the night) had dropped it from the tracked set.
            restored_on = {
                entity_id
                for entity_id, saved in self._sleep_snapshot.items()
                if saved.get("state") == STATE_ON
            }
            restored_off = set(self._sleep_snapshot) - restored_on
            self.auto_lights.update(
                ((self._lights_on() | restored_on) - restored_off)
                - self.manual_overrides
            )
            self._schedule_persistent_state_save()
            self.light_reason = "Restored pre-sleep state of changed lights"
        else:
            transition = float(self.config.get(
                CONF_SLEEP_RESTORE_TRANSITION,
                DEFAULT_SLEEP_RESTORE_TRANSITION,
            ))
            await self._turn_off_all_lights(transition)
            if not self.occupied and self.enabled and self.mode != "disabled":
                # Same Area sweep as a normal vacancy.
                leftover = {
                    entity_id
                    for entity_id in self.turned_on_lights
                    if self._light_is_on(entity_id)
                }
                self.turned_on_lights -= leftover
                if leftover:
                    await self.hass.services.async_call(
                        "light", "turn_off",
                        {ATTR_ENTITY_ID: list(leftover), "transition": transition},
                        blocking=False,
                    )
            self.light_reason = "Sleep ended; lighting not needed"

        self._sleep_snapshot = {}
        await self._save_sleep_state()

    async def _apply_sleep_profile(self) -> None:
        profiles = self.config.get(CONF_SLEEP_LIGHT_PROFILES, {})
        sleep_lights = set(self.config.get(CONF_SLEEP_LIGHTS, []))
        transition = float(
            self.config.get(CONF_SLEEP_TRANSITION, DEFAULT_SLEEP_TRANSITION)
        )

        # Do not send turn_off to lights that are already off. This keeps the
        # snapshot limited to lights whose state/profile is actually changed.
        changed_lights = self._lights_changed_by_sleep_profile()
        to_off = {
            entity_id
            for entity_id in changed_lights
            if entity_id not in sleep_lights
            or not profiles.get(entity_id, {}).get(CONF_SLEEP_LIGHT_ON, True)
        }
        if to_off:
            await self.hass.services.async_call(
                "light", "turn_off",
                {ATTR_ENTITY_ID: list(to_off), "transition": transition},
                blocking=False,
            )

        for entity_id in sleep_lights & changed_lights:
            profile = profiles.get(entity_id, {})
            if not profile.get(CONF_SLEEP_LIGHT_ON, True):
                continue
            data: dict[str, Any] = {
                ATTR_ENTITY_ID: entity_id,
                "transition": transition,
            }
            brightness_pct = profile.get(CONF_SLEEP_BRIGHTNESS)
            if brightness_pct is not None:
                data["brightness_pct"] = int(brightness_pct)
            color_mode = profile.get(CONF_SLEEP_COLOR_MODE)
            if color_mode == SLEEP_COLOR_RGB and profile.get(CONF_SLEEP_RGB_COLOR):
                data[ATTR_RGB_COLOR] = profile[CONF_SLEEP_RGB_COLOR]
            elif color_mode == SLEEP_COLOR_TEMP and profile.get(CONF_SLEEP_COLOR_TEMP):
                data[ATTR_COLOR_TEMP_KELVIN] = int(profile[CONF_SLEEP_COLOR_TEMP])
            await self.hass.services.async_call("light", "turn_on", data, blocking=False)

    async def _restore_light_snapshot(self) -> None:
        transition = float(
            self.config.get(
                CONF_SLEEP_RESTORE_TRANSITION, DEFAULT_SLEEP_RESTORE_TRANSITION
            )
        )
        for entity_id, saved in self._sleep_snapshot.items():
            if saved.get("state") != STATE_ON:
                await self.hass.services.async_call(
                    "light", "turn_off",
                    {ATTR_ENTITY_ID: entity_id, "transition": transition},
                    blocking=False,
                )
                continue
            data: dict[str, Any] = {
                ATTR_ENTITY_ID: entity_id,
                "transition": transition,
            }
            if saved.get(ATTR_BRIGHTNESS) is not None:
                data[ATTR_BRIGHTNESS] = saved[ATTR_BRIGHTNESS]
            color_mode = saved.get(ATTR_COLOR_MODE)
            if saved.get(ATTR_RGB_COLOR) is not None and color_mode in (
                "rgb", "rgbw", "rgbww"
            ):
                data[ATTR_RGB_COLOR] = saved[ATTR_RGB_COLOR]
            elif saved.get(ATTR_XY_COLOR) is not None and color_mode == "xy":
                data[ATTR_XY_COLOR] = saved[ATTR_XY_COLOR]
            elif saved.get(ATTR_HS_COLOR) is not None and color_mode == "hs":
                data[ATTR_HS_COLOR] = saved[ATTR_HS_COLOR]
            elif saved.get(ATTR_COLOR_TEMP_KELVIN) is not None:
                data[ATTR_COLOR_TEMP_KELVIN] = saved[ATTR_COLOR_TEMP_KELVIN]
            await self.hass.services.async_call("light", "turn_on", data, blocking=False)

    async def _turn_off_all_lights(self, transition: float = 0) -> None:
        lights = self._all_lights()
        if not lights:
            return
        data: dict[str, Any] = {ATTR_ENTITY_ID: list(lights)}
        if transition > 0:
            data["transition"] = transition
        await self.hass.services.async_call("light", "turn_off", data, blocking=False)
        self.auto_lights.clear()
        self._schedule_persistent_state_save()

    async def _handle_vacant(self) -> None:
        """Apply vacancy behavior, including optional automatic sleep-mode exit."""
        # The next Vacant -> Occupied transition starts a fresh lighting cycle.
        self._lighting_profile_applied = False
        self.manual_overrides.clear()
        if self.sleep_mode:
            await self._turn_off_all_lights(
                float(self.config.get(CONF_SLEEP_TRANSITION, DEFAULT_SLEEP_TRANSITION))
            )
            if self.sleep_auto_off:
                # Keep the snapshot until _exit_sleep_mode has made its occupied/light
                # decision. As the room is vacant, it will switch all lights off and
                # then clear the snapshot without restoring it.
                await self.async_set_sleep_mode(False)
                return
        else:
            await self.async_apply()
            if self.enabled and self.mode != "disabled":
                # Vacancy also switches off Area lights that were switched on
                # during the cycle by hand or by something other than ARM.
                # Lights that were never switched on are left alone.
                leftover = {
                    entity_id
                    for entity_id in self.turned_on_lights
                    if self._light_is_on(entity_id)
                }
                # A light that cannot be reached now stays tracked, so it is
                # switched off if it comes back on.
                self.turned_on_lights = {
                    entity_id
                    for entity_id in self.turned_on_lights
                    if self._light_is_lost(entity_id)
                }
                if leftover:
                    await self.hass.services.async_call(
                        "light", "turn_off", {ATTR_ENTITY_ID: list(leftover)},
                        blocking=False,
                    )
                    self.auto_lights.difference_update(leftover)
                    self._schedule_persistent_state_save()
        self._notify()

    def _update_presence(self, *, schedule_timer: bool = True) -> None:
        triggers, persistent = self._active_presence()

        if not self.occupied:
            self._cancel_absence_timer()
            if triggers and persistent:
                self.occupied = True
                self.presence_reason = (
                    f"Activated by trigger {triggers[0]} and persistent {persistent[0]}"
                )
                if self.sleep_mode:
                    self.hass.async_create_task(self._apply_sleep_profile())
                    self._sleep_profile_applied = True
            elif triggers:
                self.presence_reason = "Waiting for a persistent presence sensor"
            elif persistent:
                self.presence_reason = "Waiting for a trigger presence sensor"
            else:
                self.presence_reason = "No active presence sensors"
            return

        if triggers or persistent:
            self._cancel_absence_timer()
            if triggers and persistent:
                self.presence_reason = (
                    f"Held by trigger {triggers[0]} and persistent {persistent[0]}"
                )
            elif triggers:
                self.presence_reason = f"Held by trigger {triggers[0]}"
            else:
                self.presence_reason = f"Held by persistent {persistent[0]}"
            return

        if not schedule_timer:
            return
        if self._absence_cancel:
            self.presence_reason = (
                "Sleep absence delay" if self.sleep_mode else "Vacancy delay"
            )
            return

        delay = self.current_absence_delay
        self.presence_reason = (
            "Sleep absence delay" if self.sleep_mode else "Vacancy delay"
        )

        @callback
        def clear_presence(_now) -> None:
            self._absence_cancel = None
            current_triggers, current_persistent = self._active_presence()
            if current_triggers or current_persistent:
                self.hass.async_create_task(self.async_evaluate())
                return
            self.occupied = False
            self.presence_reason = (
                "Sleep absence delay expired"
                if self.sleep_mode
                else "Absence delay expired"
            )
            self.hass.async_create_task(self._handle_vacant())

        self._absence_cancel = async_call_later(self.hass, delay, clear_presence)

    def _update_light_need(self) -> None:
        lights_on = self._lights_on()
        lux_values: list[float] = []
        for entity_id in self.config.get(CONF_LUX, []):
            state = self.hass.states.get(entity_id)
            try:
                lux_values.append(float(state.state))
            except (TypeError, ValueError, AttributeError):
                continue

        lux_settled = self.hass.loop.time() >= self._lux_settle_until
        if not lights_on and lux_values and lux_settled:
            self.last_natural_lux = sum(lux_values) / len(lux_values)

        valid_covers = []
        for entity_id in self.config.get(CONF_COVERS, []):
            state = self.hass.states.get(entity_id)
            if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                valid_covers.append(state)
        any_open = any(state.state != STATE_CLOSED for state in valid_covers)

        sun = self.hass.states.get("sun.sun")
        try:
            elevation = float(sun.attributes.get("elevation", 0)) if sun else 0
        except (TypeError, ValueError):
            elevation = 0

        period = self.period()
        if period == "night":
            self.light_needed = True
            self.light_reason = "Night profile"
        elif self.last_natural_lux is not None:
            self.light_needed = self.last_natural_lux < self.lux_threshold
            self.light_reason = f"Stored natural lux: {self.last_natural_lux:.1f} lx"
        else:
            self.light_needed = not (any_open and elevation > 3)
            self.light_reason = "Cover and sun fallback"

    async def async_evaluate(
        self, changed: str | None = None, *, period_boundary: bool = False
    ) -> None:
        was_occupied = self.occupied
        previous_period = self._last_period
        current_period = self.period()
        period_changed = previous_period is not None and current_period != previous_period
        self._last_period = current_period

        self._update_presence()
        self._update_light_need()

        if self.sleep_mode:
            self.sleep_reason = "Enabled by the room Sleep mode switch"
            if self.occupied and (not was_occupied or not self._sleep_profile_applied):
                await self._apply_sleep_profile()
                self._sleep_profile_applied = True
        else:
            await self.async_apply(
                current_period=current_period,
                period_changed=period_changed or period_boundary,
            )

        self._notify()

    def _sync_enabled_for_period(self, period: str) -> bool:
        settings = {
            "day": (CONF_SYNC_ENTER_DAY, DEFAULT_SYNC_ENTER_DAY),
            "evening": (CONF_SYNC_ENTER_EVENING, DEFAULT_SYNC_ENTER_EVENING),
            "night": (CONF_SYNC_ENTER_NIGHT, DEFAULT_SYNC_ENTER_NIGHT),
        }
        key, default = settings[period]
        return bool(self.config.get(key, default))

    async def async_apply(
        self, *, current_period: str | None = None, period_changed: bool = False
    ) -> None:
        if not self.enabled or self.mode == "disabled" or self.sleep_mode:
            return

        groups = {
            "day": CONF_DAY_LIGHTS,
            "evening": CONF_EVENING_LIGHTS,
            "night": CONF_NIGHT_LIGHTS,
        }
        current_period = current_period or self.period()
        active_lighting = self.occupied and self.light_needed
        desired = (
            set(self.config.get(groups[current_period], [])) if active_lighting else set()
        )
        currently_on = self._lights_on()
        synchronize_period = (
            active_lighting
            and period_changed
            and self._sync_enabled_for_period(current_period)
        )

        # A profile may turn lights on only once per occupancy cycle. An enabled
        # period transition is the deliberate exception: it synchronizes the new
        # Day/Evening/Night profile. Ordinary state, lux, cover and presence events
        # must not re-enable a light that the user switched off manually.
        may_apply_profile = active_lighting and (
            not self._lighting_profile_applied or synchronize_period
        )
        to_on = (
            (desired - currently_on) - self.manual_overrides
            if may_apply_profile
            else set()
        )

        if not active_lighting:
            # Vacancy or sufficient natural light clears only lights ARM previously
            # switched on. The one-shot flag is reset only when vacancy is confirmed,
            # not by a temporary lux change while the room remains occupied.
            to_off = self.auto_lights - self.manual_overrides
        elif synchronize_period:
            # Synchronize every managed light when the option for the newly entered
            # period is enabled.
            to_off = (currently_on - desired) - self.manual_overrides
        else:
            # No maintenance commands while the same occupancy cycle continues.
            to_off = set()

        auto_before = set(self.auto_lights)
        if to_on:
            await self.hass.services.async_call(
                "light", "turn_on", {ATTR_ENTITY_ID: list(to_on)}, blocking=False
            )
            self.auto_lights.update(to_on)
        if may_apply_profile:
            # Profile lights that were already on when the cycle started (switched
            # on by hand, by another automation, or left on) are adopted, so they
            # are switched off on vacancy like the ones ARM turned on itself.
            self.auto_lights.update((desired & currently_on) - self.manual_overrides)
        if to_off:
            await self.hass.services.async_call(
                "light", "turn_off", {ATTR_ENTITY_ID: list(to_off)}, blocking=False
            )
            self.auto_lights.difference_update(
                {
                    entity_id
                    for entity_id in to_off
                    if not self._light_is_lost(entity_id)
                }
            )
        if self.auto_lights != auto_before:
            self._schedule_persistent_state_save()

        if may_apply_profile:
            # Mark the attempt as applied even when all desired lights were already
            # on. This ensures subsequent manual OFF actions remain respected.
            self._lighting_profile_applied = True

    def _notify(self) -> None:
        for callback_func in list(self.callbacks):
            callback_func()
