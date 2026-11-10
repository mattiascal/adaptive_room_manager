"""Constants for Adaptive Room Manager."""

DOMAIN = "adaptive_room_manager"
NAME = "Adaptive Room Manager"
MANUFACTURER = "Adaptive Room Manager"
MODEL = "Adaptive Room"
VERSION = "0.6.8"
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
# Home Settings: how the stored natural illuminance is recorded.
CONF_LUX_PRECISION = "lux_precision"
CONF_LUX_UPDATE_INTERVAL = "natural_lux_update_interval"

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
DEFAULT_LUX_PRECISION = 0
DEFAULT_LUX_UPDATE_INTERVAL = 300
DEFAULT_SLEEP_ABSENCE_DELAY = 30
DEFAULT_SLEEP_AUTO_OFF = False
DEFAULT_SLEEP_TRANSITION = 3.0
DEFAULT_SLEEP_RESTORE_TRANSITION = 3.0

# Seconds to wait before a lux reading is trusted: after a light went off, and
# after Sleep mode ended (while the sleep lights are held in SLEEP_EXIT_RGB_COLOR).
LUX_SETTLE_SECONDS = 10
SLEEP_EXIT_RGB_COLOR = (255, 140, 0)
# Lights without color support run one of these effects (first one the light
# offers) for a few seconds, then one of the stop effects if it offers any.
# Without effects they use the light's own flash, without flash they blink.
SLEEP_EXIT_EFFECTS = ("breathe", "blink", "pulse", "flash", "okay", "strobe")
SLEEP_EXIT_EFFECT_STOPS = ("stop_effect", "finish_effect", "none", "off", "solid")
SLEEP_EXIT_EFFECT_SECONDS = 3
LIGHT_FEATURE_FLASH = 8  # LightEntityFeature.FLASH
SLEEP_EXIT_BLINKS = 3
SLEEP_EXIT_BLINK_SECONDS = 0.5

# Seconds during which a light coming on is attributed to ARM's own command.
ARM_COMMAND_WINDOW_SECONDS = 15

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.sleep"

# Label id: lights carrying it are never switched off by the vacancy Area sweep.
AREA_OFF_EXCLUDE_LABEL = "arm_exclude"
