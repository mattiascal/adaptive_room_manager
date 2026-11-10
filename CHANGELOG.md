# Changelog

## 0.6.8

- Switching Sleep mode off now resumes the room's normal lighting rules, as if someone had just entered. The room is occupied and a fresh lighting cycle starts; with no presence sensor active the normal absence delay runs and vacancy switches the lights off as usual. This replaces the 0.6.6 behavior (presence cleared at once when no sensor was active).
- If lighting is needed, the lights that are not part of the current Day/Evening/Night profile are switched off and the profile lights are switched on with a plain `light.turn_on`, so Adaptive Lighting (or the light itself) decides brightness and color. The pre-sleep state of the lights is no longer restored.
- If lighting is not needed, all managed lights are switched off and presence stays active.
- The stored natural illuminance is refreshed when Sleep mode ends instead of reusing the value from the evening before; if that reading was inflated by the sleep lights it is sampled again once they are off.
- Automatic Sleep mode exit on vacancy still switches everything off without assuming presence.

## 0.6.7

- Stored natural illuminance is rounded and rate limited, so small sensor fluctuations (e.g. 6.1 ↔ 6.3 lx) no longer update the Lighting reason and Stored natural illuminance sensors every few seconds and flood the recorder.
- New Home Settings: **Stored lux decimals** (default 0, whole lux) and **Stored lux update interval** (default 300 s). A reading that crosses a room lux threshold is always stored at once, so lighting decisions are not delayed.
- Manifest documentation and issue tracker now point to `mattiascal/adaptive_room_manager`.

## 0.6.6

- Leaving Sleep mode with no presence sensor active now ends the occupancy cycle immediately: the room was only being held by the Sleep absence delay, so all managed lights (and tracked Area lights) are switched off instead of being restored or switched on for an empty room.
- Lights left on after Sleep mode ends in an occupied room are now tracked and switched off on vacancy, even if Sleep mode or a restart during the night had dropped them from the tracked set.
- Restart handling: lights still unavailable/unknown when ARM starts are no longer dropped from the tracked set, a light that reappears already on is tracked, and if the room is vacant it is switched off after the absence delay. Lights that cannot be reached at vacancy stay tracked.
- Natural illuminance is no longer sampled during the 30 seconds after a light goes off. This fixes lights being switched back on right after ARM turned them off, because the lux sensor still reported the artificial light.

## 0.6.5

- Fixed room lights staying on after vacancy when they were already on at the start of an occupancy cycle (switched on by hand, by another automation, or left on). Lights of the active profile that are already on are now adopted and switched off when the room becomes vacant.
- The set of lights ARM switches off on vacancy is now persisted. After a Home Assistant restart, if those lights are still on, the occupancy cycle resumes and the normal absence delay switches them off once the room is empty.
- On vacancy (outside Sleep mode) ARM also switches off lights of the room's Area that were switched on during the cycle by hand, by an app or by another automation, even if they are not configured in any profile. Lights that were never switched on are left alone. Area membership follows the entity's Area or, if unset, its device's Area. Light groups, config/diagnostic light entities and lights labelled `arm_exclude` are ignored. The tracked set is persisted across restarts.

## 0.6.4

- Added persistent storage for the last known state of every light managed by a room.
- After Home Assistant starts, Adaptive Room Manager waits for entity restoration and then restores each managed light to its pre-restart on/off, brightness and color state.
- Startup restoration preserves manual light changes and prevents the active Day, Evening, Night or Sleep profile from immediately overwriting a restored occupied-room state.
- Light-state persistence is updated as managed lights change and is also flushed when the room manager unloads.
- Kept the 0.6.3 interface, Area icons and local brand assets unchanged. The controller refactor remains deferred to 0.6.5.

## 0.6.3

- Renamed the global configuration entry to `★ Home Settings` so it sorts before room entries in Home Assistant. Existing Home Settings entries are renamed automatically when the integration loads.
- Room entities now use the icon configured on their linked Home Assistant Area.
- Added local integration brand icons for light and dark themes, including high-resolution variants.
- Kept the 0.6.2 Options Flow reload fix and all 0.6.1 room behavior unchanged.

## 0.6.2

- Fixed saving Home Settings and room options on Home Assistant versions that reject config entry update listeners together with `OptionsFlowWithReload`.
- Changed the options flow to the standard `OptionsFlow`, retaining the existing update listener so Home Settings changes still reload all room entries and re-register the Morning, Evening and Night schedules.
- No lighting, presence, lux or Sleep mode behavior was otherwise changed from 0.6.1.

## 0.6.1

- Changed normal lighting to a one-shot profile per occupancy cycle: after ARM applies the Day, Evening or Night profile, later evaluations no longer resend `light.turn_on`.
- A light switched off manually while the room remains occupied stays off until the user turns it on again or the room becomes vacant and is occupied again.
- Enabled Day/Evening/Night transition synchronization remains an explicit exception and may apply the newly entered profile.
- Reset the one-shot lighting cycle only after the configured absence delay expires and the room becomes vacant.
- Fixed the room entity-list builder so boolean period-synchronization options are not treated as entity lists.
- Fixed the room Options menu labels and added a root `strings.json` translation source.
- Added exact daily scheduling at Morning, Evening and Night boundaries.
- Added per-room synchronization switches for entering Day, Evening and Night.
- When synchronization is enabled, managed lights outside the new period profile are turned off and missing profile lights are turned on when lighting is required.
- When synchronization is disabled, lights retained from the previous period are not removed merely because the period changed.
- Home Settings changes now reload room entries so period schedules are registered again.
- Refined Sleep mode snapshots so only lights whose state, brightness or color will actually change are saved.
- Avoided sending Sleep mode commands to lights already matching their configured sleep profile.

## 0.6.0

- Replaced external sleep activation entities with a room-owned `Sleep mode` switch.
- Removed forced sleep occupancy.
- Replaced the forced occupancy timeout with `Sleep absence delay`.
- While Sleep mode is active, the sleep absence delay replaces the room's normal absence delay after all presence sensors become inactive.
- Added an option to turn off the room Sleep mode switch automatically when the room becomes vacant.
- Managed lights are switched off when the room becomes vacant, even when Sleep mode remains enabled.
- Sleep lighting is reapplied when the room becomes occupied again while Sleep mode remains enabled.
- Pre-sleep snapshots now include only lights that Sleep mode actually changes.
- Added migration from 0.5.x settings.

## 0.5.0

- Added sleep mode with per-light brightness, RGB color, color temperature and transitions.
- Added persistent pre-sleep light snapshots.
