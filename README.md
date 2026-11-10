# Adaptive Room Manager

Adaptive Room Manager is a HACS custom integration for Home Assistant. It turns existing Home Assistant Areas into room devices with occupancy, natural-light, adaptive lighting and sleep-mode behavior. Configuration is performed from the Home Assistant UI; no helpers, blueprints or template sensors are required by the integration.

## Architecture

The integration creates:

- one global **Home Settings** config entry;
- one **Room** config entry for each selected Home Assistant Area;
- one Home Assistant device for every configured room.

Home Settings contain the global Morning, Evening and Night schedule plus defaults for new rooms. Each room keeps its own presence sensors, lux sensors, covers, lights, lux threshold, normal absence delay and Sleep mode settings.

## Presence model

A vacant room becomes occupied only when both conditions are true:

1. at least one Trigger presence sensor is active;
2. at least one Persistent presence sensor is active.

The same entity may be selected in both groups. Once occupied, any active sensor from either group keeps the room occupied. When every sensor becomes inactive, the appropriate absence delay starts.

- With Sleep mode off, the room uses its normal **Absence delay** in seconds.
- With Sleep mode on, the room uses **Sleep absence delay** in minutes instead.

Any sensor becoming active before the delay expires cancels the timer. The room becomes vacant only if all presence sensors are still inactive when the selected delay expires.

## Natural-light model

Natural illuminance is sampled only while all managed lights are off. The latest valid average is retained and compared with the room lux threshold. The retained value is rounded to **Stored lux decimals** and changes at most once per **Stored lux update interval** (Home Settings, default whole lux and 300 s); a reading that crosses the room threshold is retained immediately. The integration never switches lights off temporarily to measure lux.

When no retained lux value exists, covers and sun elevation provide a fallback:

- unavailable or unknown covers are ignored;
- a closed cover is treated as shaded;
- any other valid cover state is treated as open.

## Normal lighting profiles

Each room can select separate light groups for Day, Evening and Night. The schedule is global and is configured only in Home Settings.

## Room Sleep mode switch

Every room device exposes its own switch:

```text
switch.<room>_sleep_mode
```

The switch is named **Sleep mode** on the room device. Adaptive Room Manager does not decide when sleeping starts or ends. Create a normal Home Assistant automation that turns this switch on or off from a bed sensor, schedule, button, alarm state or any other condition.

Conceptual automation:

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.bed_occupied
    to: "on"
actions:
  - action: switch.turn_on
    target:
      entity_id: switch.bedroom_sleep_mode
```

Use the reverse state and `switch.turn_off` to leave Sleep mode.

## Period transition synchronization

Each room has three independent options for entering Day, Evening and Night.
When an option is enabled, Adaptive Room Manager synchronizes managed lights at
the exact configured boundary: lights outside the new profile are switched off
and missing lights in the new profile are switched on when the room is occupied
and artificial light is needed. When an option is disabled, lights retained from
the previous period are not switched off merely because the period changed.


## Sleep absence delay

Sleep mode replaces only the vacancy timer.

Example:

- Normal absence delay: 60 seconds
- Sleep absence delay: 30 minutes

With Sleep mode on, when every presence sensor becomes inactive, the room waits 30 minutes before becoming vacant. Normal trigger and persistent activation rules remain unchanged.

The option **Turn off Sleep mode when room becomes vacant** controls what happens when the sleep absence delay expires:

- enabled: the integration turns off its own Sleep mode switch;
- disabled: Sleep mode remains on, but all managed lights are switched off while the room is vacant.

If the room becomes occupied again while Sleep mode remains on, the configured sleep lighting profile is applied again.

## Sleep lighting profiles

Sleep settings let you choose sleep lights and configure each selected light individually:

- on or off;
- brightness percentage;
- keep current color;
- RGB color using the Home Assistant color picker;
- white color temperature in Kelvin;
- enter-sleep transition;
- restore transition.

When Sleep mode turns on, the integration switches off currently-on managed lights that are not part of the active sleep profile and applies the configured sleep state to the selected sleep lights.

### Selective pre-sleep snapshot

The integration saves only lights that Sleep mode actually changes:

- sleep lights configured to turn on or receive brightness/color settings;
- currently-on lights that Sleep mode switches off.

Lights that are already off and receive no command are not stored. The snapshot is captured once when Sleep mode turns on and is persisted in Home Assistant internal storage.

When Sleep mode turns off:

- if the room is occupied and needs artificial light, only the saved lights are restored to their pre-sleep on/off, brightness and color state;
- if the room is vacant or does not need light, all managed room lights are switched off.

## Room entities

A room device exposes entities including:

- Presence
- Light needed
- Sleep mode
- Automation
- Presence reason
- Lighting reason
- Sleep reason
- Period
- Stored natural illuminance
- Absence delay
- Sleep absence delay
- Illuminance threshold
- Mode

## Restart-safe light state

Adaptive Room Manager stores the last valid state of every light managed by each room. After Home Assistant has completed startup, the integration restores those lights to their pre-restart state, including on/off state, brightness and supported color information.

This restoration is independent from the current Day, Evening or Night period. For example, if Home Assistant restarts during Night while one room light has been manually switched off and another is on at a custom brightness, those states are restored instead of immediately reapplying the full Night profile. If the room is already occupied at startup, the restored state is treated as the already-applied lighting state for that occupancy cycle.

Lights that are unavailable or unknown when restoration runs are left unchanged rather than receiving an unsafe command.

## Installation with HACS

1. Open HACS.
2. Add `https://github.com/Mattiabatto/adaptive_room_manager` as a custom repository of category **Integration**.
3. Download Adaptive Room Manager.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Add Home Settings, then add one Room entry for each Area.

## Updating

Publish a GitHub Release whose tag matches the integration version, for example `v0.6.0`. In HACS, use **Update information** if the release is not detected immediately, then install the available update and restart Home Assistant.

## Migration from 0.5.x

Version 0.6.0 automatically:

- removes the old external Sleep mode entity selection;
- removes forced sleep occupancy;
- converts the previous timeout value into the new Sleep absence delay value;
- preserves sleep light selections, profiles, transitions and saved snapshots;
- exposes the new room-owned Sleep mode switch.

Review the Sleep mode options after upgrading because the migrated timeout now represents a vacancy delay, not a forced-occupancy duration.

## License

MIT License. Copyright Mattia Batto.

## One-shot lighting per occupancy cycle

When a vacant room becomes occupied and lighting is needed, Adaptive Room Manager applies the current Day, Evening or Night profile once. It does not continuously maintain that profile.

If a user switches off one of those lights while the room remains occupied, the integration leaves it off during later presence, lux, cover and light-state updates. The lighting cycle resets only after all presence is lost, the applicable absence delay expires, and the room becomes vacant. On the next valid occupancy activation, the current profile can be applied again.

An enabled period-transition synchronization option is an intentional exception: entering Day, Evening or Night may synchronize the newly selected profile. Sleep Mode also retains its own explicit enter/exit behavior.

## Home Assistant UI integration

Adaptive Room Manager names the global entry **★ Home Settings** so it appears before alphabetically sorted room entries. Existing installations are updated automatically when the integration loads.

Every entity created for a room uses the icon configured on the linked Home Assistant Area. If the Area has no icon, Home Assistant falls back to the entity domain or device-class icon.

The integration ships local light- and dark-theme brand icons in `custom_components/adaptive_room_manager/brand/`. These are supported by Home Assistant 2026.3 and newer.
