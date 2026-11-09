"""Constants for Adaptive Room Manager."""

DOMAIN = "adaptive_room_manager"
NAME = "Adaptive Room Manager"
MANUFACTURER = "Adaptive Room Manager"
MODEL = "Adaptive Room"
VERSION = "0.6.4"
PLATFORMS = ["binary_sensor", "sensor", "switch", "number", "select"]

CONF_ENTRY_TYPE = "entry_type"
ENTRY_TYPE_HOME = "home"
ENTRY_TYPE_ROOM = "room"
HOME_UNIQUE_ID = "home_settings"
HOME_TITLE = "★ Home Settings"

CONF_AREA_ID = "area_id"
CONF_TRIGGER_PRESENCE = "trigger_presence_sensors"
CONF_PERSISTENT = "persistent_presence_sensors"
CONF_LEGACY_TEMPORARY = "temporary_presence"
CONF_LEGACY_PERSISTENT = "persistent_presence"
CONF_LUX = "lux_sensors"
CONF_COVERS = "covers"
CONF_DAY_LIGHTS = "day_lights"
CONF_EVENING_LIGHTS = "evening_lights"
CONF_NIGHT_LIGHTS = "night_lights"
CONF_EVENING_START = "evening_start"
CONF_NIGHT_START = "night_start"
CONF_MORNING_START = "morning_start"
CONF_LUX_THRESHOLD = "lux_threshold"
CONF_ABSENCE_DELAY = "absence_delay"

# Period transition behavior. When enabled for the period being entered, the
# room synchronizes managed lighting by turning off lights outside that profile.
CONF_SYNC_ENTER_DAY = "sync_lights_entering_day"
CONF_SYNC_ENTER_EVENING = "sync_lights_entering_evening"
CONF_SYNC_ENTER_NIGHT = "sync_lights_entering_night"
DEFAULT_SYNC_ENTER_DAY = True
DEFAULT_SYNC_ENTER_EVENING = True
DEFAULT_SYNC_ENTER_NIGHT = True

# Sleep mode is exposed by the integration as a room switch. The legacy
# external-entity and forced-occupancy settings are retained only for migration.
CONF_LEGACY_SLEEP_ENTITIES = "sleep_mode_entities"
CONF_LEGACY_SLEEP_TIMEOUT = "sleep_occupancy_timeout"
CONF_SLEEP_ABSENCE_DELAY = "sleep_absence_delay"
CONF_SLEEP_AUTO_OFF = "sleep_auto_off_when_vacant"
CONF_SLEEP_LIGHTS = "sleep_lights"
CONF_SLEEP_LIGHT_PROFILES = "sleep_light_profiles"
CONF_SLEEP_TRANSITION = "sleep_transition"
CONF_SLEEP_RESTORE_TRANSITION = "sleep_restore_transition"
CONF_SLEEP_LIGHT_ON = "on"
CONF_SLEEP_BRIGHTNESS = "brightness"
CONF_SLEEP_COLOR_MODE = "color_mode"
CONF_SLEEP_RGB_COLOR = "rgb_color"
CONF_SLEEP_COLOR_TEMP = "color_temp_kelvin"

SLEEP_COLOR_KEEP = "keep"
SLEEP_COLOR_RGB = "rgb"
SLEEP_COLOR_TEMP = "color_temp"

DEFAULT_EVENING_START = "18:00:00"
DEFAULT_NIGHT_START = "22:30:00"
DEFAULT_MORNING_START = "07:00:00"
DEFAULT_LUX_THRESHOLD = 40.0
DEFAULT_ABSENCE_DELAY = 600
DEFAULT_SLEEP_ABSENCE_DELAY = 30
DEFAULT_SLEEP_AUTO_OFF = False
DEFAULT_SLEEP_TRANSITION = 3.0
DEFAULT_SLEEP_RESTORE_TRANSITION = 3.0

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.sleep"

# Label id: lights carrying it are never switched off by the vacancy Area sweep.
AREA_OFF_EXCLUDE_LABEL = "arm_exclude"
