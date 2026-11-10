"""Config and options flows for Adaptive Room Manager."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.helpers import area_registry as ar, selector

from .const import (
    CONF_ABSENCE_DELAY,
    CONF_AREA_ID,
    CONF_COVERS,
    CONF_DAY_LIGHTS,
    CONF_ENTRY_TYPE,
    CONF_EVENING_LIGHTS,
    CONF_EVENING_START,
    CONF_LUX,
    CONF_LUX_THRESHOLD,
    CONF_LUX_PRECISION,
    CONF_LUX_UPDATE_INTERVAL,
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
    DEFAULT_LUX_PRECISION,
    DEFAULT_LUX_UPDATE_INTERVAL,
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
    ENTRY_TYPE_ROOM,
    HOME_TITLE,
    HOME_UNIQUE_ID,
    SLEEP_COLOR_KEEP,
    SLEEP_COLOR_RGB,
    SLEEP_COLOR_TEMP,
)


def _home_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_EVENING_START,
                default=defaults.get(CONF_EVENING_START, DEFAULT_EVENING_START),
            ): selector.TimeSelector(),
            vol.Required(
                CONF_NIGHT_START,
                default=defaults.get(CONF_NIGHT_START, DEFAULT_NIGHT_START),
            ): selector.TimeSelector(),
            vol.Required(
                CONF_MORNING_START,
                default=defaults.get(CONF_MORNING_START, DEFAULT_MORNING_START),
            ): selector.TimeSelector(),
            vol.Required(
                CONF_LUX_THRESHOLD,
                default=defaults.get(CONF_LUX_THRESHOLD, DEFAULT_LUX_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=2000,
                    step=1,
                    unit_of_measurement="lx",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_ABSENCE_DELAY,
                default=defaults.get(CONF_ABSENCE_DELAY, DEFAULT_ABSENCE_DELAY),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=7200,
                    step=10,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_LUX_PRECISION,
                default=defaults.get(CONF_LUX_PRECISION, DEFAULT_LUX_PRECISION),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=2, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_LUX_UPDATE_INTERVAL,
                default=defaults.get(
                    CONF_LUX_UPDATE_INTERVAL, DEFAULT_LUX_UPDATE_INTERVAL
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=3600,
                    step=30,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _room_schema(defaults: dict[str, Any], *, include_area: bool) -> vol.Schema:
    fields: dict[Any, Any] = {}
    if include_area:
        fields[vol.Required(CONF_AREA_ID)] = selector.AreaSelector()

    fields.update(
        {
            vol.Optional(
                CONF_TRIGGER_PRESENCE, default=defaults.get(CONF_TRIGGER_PRESENCE, [])
            ): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True)),
            vol.Optional(
                CONF_PERSISTENT, default=defaults.get(CONF_PERSISTENT, [])
            ): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True)),
            vol.Optional(CONF_LUX, default=defaults.get(CONF_LUX, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            ),
            vol.Optional(
                CONF_COVERS, default=defaults.get(CONF_COVERS, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="cover", multiple=True)
            ),
            vol.Optional(
                CONF_DAY_LIGHTS, default=defaults.get(CONF_DAY_LIGHTS, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="light", multiple=True)
            ),
            vol.Optional(
                CONF_EVENING_LIGHTS, default=defaults.get(CONF_EVENING_LIGHTS, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="light", multiple=True)
            ),
            vol.Optional(
                CONF_NIGHT_LIGHTS, default=defaults.get(CONF_NIGHT_LIGHTS, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="light", multiple=True)
            ),
            vol.Required(
                CONF_SYNC_ENTER_DAY,
                default=defaults.get(CONF_SYNC_ENTER_DAY, DEFAULT_SYNC_ENTER_DAY),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_SYNC_ENTER_EVENING,
                default=defaults.get(
                    CONF_SYNC_ENTER_EVENING, DEFAULT_SYNC_ENTER_EVENING
                ),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_SYNC_ENTER_NIGHT,
                default=defaults.get(CONF_SYNC_ENTER_NIGHT, DEFAULT_SYNC_ENTER_NIGHT),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_LUX_THRESHOLD,
                default=defaults.get(CONF_LUX_THRESHOLD, DEFAULT_LUX_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=2000,
                    step=1,
                    unit_of_measurement="lx",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_ABSENCE_DELAY,
                default=defaults.get(CONF_ABSENCE_DELAY, DEFAULT_ABSENCE_DELAY),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=7200,
                    step=10,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )
    return vol.Schema(fields)


def _sleep_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_SLEEP_ABSENCE_DELAY,
                default=defaults.get(
                    CONF_SLEEP_ABSENCE_DELAY, DEFAULT_SLEEP_ABSENCE_DELAY
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=1440,
                    step=1,
                    unit_of_measurement="min",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_SLEEP_AUTO_OFF,
                default=defaults.get(CONF_SLEEP_AUTO_OFF, DEFAULT_SLEEP_AUTO_OFF),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_SLEEP_LIGHTS, default=defaults.get(CONF_SLEEP_LIGHTS, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="light", multiple=True)
            ),
            vol.Required(
                CONF_SLEEP_TRANSITION,
                default=defaults.get(CONF_SLEEP_TRANSITION, DEFAULT_SLEEP_TRANSITION),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=300,
                    step=0.5,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_SLEEP_RESTORE_TRANSITION,
                default=defaults.get(
                    CONF_SLEEP_RESTORE_TRANSITION,
                    DEFAULT_SLEEP_RESTORE_TRANSITION,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=300,
                    step=0.5,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _sleep_light_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_SLEEP_LIGHT_ON,
                default=defaults.get(CONF_SLEEP_LIGHT_ON, True),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_SLEEP_BRIGHTNESS,
                default=defaults.get(CONF_SLEEP_BRIGHTNESS, 10),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    step=1,
                    unit_of_measurement="%",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
            vol.Required(
                CONF_SLEEP_COLOR_MODE,
                default=defaults.get(CONF_SLEEP_COLOR_MODE, SLEEP_COLOR_KEEP),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[SLEEP_COLOR_KEEP, SLEEP_COLOR_RGB, SLEEP_COLOR_TEMP],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="sleep_color_mode",
                )
            ),
            vol.Required(
                CONF_SLEEP_RGB_COLOR,
                default=defaults.get(CONF_SLEEP_RGB_COLOR, [0, 0, 255]),
            ): selector.selector({"color_rgb": {}}),
            vol.Required(
                CONF_SLEEP_COLOR_TEMP,
                default=defaults.get(CONF_SLEEP_COLOR_TEMP, 2200),
            ): selector.selector(
                {
                    "color_temp": {
                        "unit": "kelvin",
                        "min": 1000,
                        "max": 10000,
                    }
                }
            ),
        }
    )


def _home_defaults(hass) -> dict[str, Any]:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HOME:
            return {**entry.data, **entry.options}
    return {}


class AdaptiveRoomManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure Adaptive Room Manager."""

    VERSION = 6

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(step_id="user", menu_options=["home", "room"])

    async def async_step_home(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(HOME_UNIQUE_ID)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(
                title=HOME_TITLE,
                data={CONF_ENTRY_TYPE: ENTRY_TYPE_HOME, **user_input},
            )
        return self.async_show_form(step_id="home", data_schema=_home_schema({}))

    async def async_step_room(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            area_id = user_input[CONF_AREA_ID]
            await self.async_set_unique_id(f"room_{area_id}")
            self._abort_if_unique_id_configured()
            area = ar.async_get(self.hass).async_get_area(area_id)
            return self.async_create_entry(
                title=area.name if area else "Adaptive Room",
                data={CONF_ENTRY_TYPE: ENTRY_TYPE_ROOM, **user_input},
            )
        return self.async_show_form(
            step_id="room",
            data_schema=_room_schema(_home_defaults(self.hass), include_area=True),
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return AdaptiveRoomManagerOptionsFlow()


class AdaptiveRoomManagerOptionsFlow(OptionsFlow):
    """Edit Home Settings or room-specific settings."""

    def __init__(self) -> None:
        self._sleep_base: dict[str, Any] = {}
        self._sleep_lights: list[str] = []
        self._sleep_index = 0
        self._sleep_profiles: dict[str, dict[str, Any]] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry_type = self.config_entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_ROOM)
        if entry_type == ENTRY_TYPE_HOME:
            return await self.async_step_home(user_input)
        return self.async_show_menu(
            step_id="init", menu_options=["room", "sleep_settings"]
        )

    async def async_step_home(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(step_id="home", data_schema=_home_schema(current))

    async def async_step_room(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            options = {**self.config_entry.options, **user_input}
            return self.async_create_entry(data=options)
        return self.async_show_form(
            step_id="room",
            data_schema=_room_schema(current, include_area=False),
        )

    async def async_step_sleep_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is None:
            return self.async_show_form(
                step_id="sleep_settings", data_schema=_sleep_schema(current)
            )

        self._sleep_base = user_input
        self._sleep_lights = list(user_input.get(CONF_SLEEP_LIGHTS, []))
        self._sleep_index = 0
        self._sleep_profiles = dict(current.get(CONF_SLEEP_LIGHT_PROFILES, {}))
        if not self._sleep_lights:
            options = {
                **self.config_entry.options,
                **self._sleep_base,
                CONF_SLEEP_LIGHT_PROFILES: {},
            }
            return self.async_create_entry(data=options)
        return await self.async_step_sleep_light()

    async def async_step_sleep_light(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entity_id = self._sleep_lights[self._sleep_index]
        if user_input is not None:
            self._sleep_profiles[entity_id] = user_input
            self._sleep_index += 1
            if self._sleep_index >= len(self._sleep_lights):
                profiles = {
                    light: self._sleep_profiles.get(light, {})
                    for light in self._sleep_lights
                }
                options = {
                    **self.config_entry.options,
                    **self._sleep_base,
                    CONF_SLEEP_LIGHT_PROFILES: profiles,
                }
                return self.async_create_entry(data=options)
            entity_id = self._sleep_lights[self._sleep_index]

        state = self.hass.states.get(entity_id)
        friendly_name = (state.attributes.get("friendly_name", entity_id) if state else entity_id)
        return self.async_show_form(
            step_id="sleep_light",
            data_schema=_sleep_light_schema(self._sleep_profiles.get(entity_id, {})),
            description_placeholders={
                "light_name": friendly_name,
                "entity_id": entity_id,
                "position": str(self._sleep_index + 1),
                "total": str(len(self._sleep_lights)),
            },
        )
