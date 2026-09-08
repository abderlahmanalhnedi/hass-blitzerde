"""Constants for the Blitzer.de integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "blitzerde"

API_URL: Final = "https://cdn2.atudo.net/api/4.0/pois.php"
API_TIMEOUT_SECONDS: Final = 15
UPSTREAM_REPAIR_FAILURE_THRESHOLD: Final = 5
REPAIR_UPSTREAM_UNAVAILABLE: Final = "upstream_unavailable"

DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 1
MAX_UPDATE_INTERVAL_MINUTES: Final = 1440

DEFAULT_SENSOR_COUNT: Final = 9
MAX_SENSOR_COUNT: Final = 50
DEFAULT_SELECTOR: Final = ".*"
DEFAULT_ONLY_CONFIRMED: Final = True
DEFAULT_NEW_MINUTES: Final = 60
MAX_NEW_MINUTES: Final = 1440
DEFAULT_BLACKLIST: Final = ""
DEFAULT_TYPES: Final = {
    "mobile": True,
    "trailer": True,
    "fixed": False,
    "archive": False,
}

CONF_KINDS: Final = "kinds"
CONTROL_KINDS: Final = {
    "speed": ("1", "7", "107", "201"),
    "redlight": ("2", "11", "111"),
    "redlight_speed": ("110",),
    "section_control": ("12", "112", "113"),
    "tunnel": ("114",),
    "distance": ("6", "101", "206"),
    "weight": ("3", "108"),
    "height": ("109",),
    "lane": ("104",),
    "entry": ("105",),
    "access": ("103",),
    "crosswalk": ("106",),
    "overtaking": ("115",),
    "police": ("4", "117"),
    "alcohol": ("5",),
    "dummy": ("102",),
    "unknown": ("0",),
}
KIND_DEFAULTS: Final = {key: True for key in CONTROL_KINDS}
CODE_KIND: Final = {
    code: kind
    for kind, codes in CONTROL_KINDS.items()
    for code in codes
}

CONF_OPTIONAL: Final = "optional"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_NEW_MINUTES: Final = "new_minutes"
CONF_BLACKLIST: Final = "blacklist"

CONF_SEARCH_MODE: Final = "search_mode"
SEARCH_MODE_AREA: Final = "area"
SEARCH_MODE_ROUTE: Final = "route"
CONF_WAYPOINTS: Final = "waypoints"
CONF_CORRIDOR_WIDTH: Final = "corridor_width"
DEFAULT_CORRIDOR_WIDTH_METERS: Final = 500
MIN_CORRIDOR_WIDTH_METERS: Final = 100
MAX_CORRIDOR_WIDTH_METERS: Final = 5000
MAX_ROUTE_QUERY_POINTS: Final = 120

ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"
ATTR_DISTANCE_KM: Final = "distance_km"

EVENT_NEW_CAMERA: Final = f"{DOMAIN}_new_camera"
SERVICE_REFRESH: Final = "refresh"

TYPE_MOBILE: Final = (0, 1, 2, 3, 4, 5, 6)
TYPE_TRAILER: Final = ("ts",)
TYPE_ARCHIVE: Final = (201, 206)
TYPE_FIXED: Final = (
    101,
    102,
    103,
    104,
    105,
    106,
    107,
    108,
    109,
    110,
    111,
    112,
    113,
    114,
    115,
    117,
)
