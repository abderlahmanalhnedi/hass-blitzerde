"""Constants for the Blitzer.de integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "blitzerde"

API_URL: Final = "https://cdn2.atudo.net/api/4.0/pois.php"
API_TIMEOUT_SECONDS: Final = 15

DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 1
MAX_UPDATE_INTERVAL_MINUTES: Final = 1440

DEFAULT_SENSOR_COUNT: Final = 9
MAX_SENSOR_COUNT: Final = 50
DEFAULT_SELECTOR: Final = ".*"
DEFAULT_ONLY_CONFIRMED: Final = True
DEFAULT_TYPES: Final = {
    "mobile": True,
    "trailer": True,
    "fixed": False,
}

CONF_OPTIONAL: Final = "optional"
CONF_UPDATE_INTERVAL: Final = "update_interval"

ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"
ATTR_DISTANCE_KM: Final = "distance_km"

EVENT_NEW_CAMERA: Final = f"{DOMAIN}_new_camera"
SERVICE_REFRESH: Final = "refresh"

TYPE_MOBILE: Final = (0, 1, 2, 3, 4, 5, 6)
TYPE_TRAILER: Final = ("ts",)
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
