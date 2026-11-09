# Changelog

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
