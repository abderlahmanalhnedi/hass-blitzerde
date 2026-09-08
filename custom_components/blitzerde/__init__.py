"""Blitzer.de custom integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_CONFIG_ENTRY_ID,
    CONF_CONDITION,
    CONF_COUNT,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_TYPE,
    Platform,
)
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .bundle import async_register_card
from .const import (
    CONF_BLACKLIST,
    CONF_NEW_MINUTES,
    CONF_SEARCH_MODE,
    CONF_UPDATE_INTERVAL,
    CONF_WAYPOINTS,
    DEFAULT_BLACKLIST,
    DEFAULT_NEW_MINUTES,
    DEFAULT_ONLY_CONFIRMED,
    DEFAULT_SELECTOR,
    DEFAULT_SENSOR_COUNT,
    DEFAULT_TYPES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    SEARCH_MODE_AREA,
    SERVICE_REFRESH,
)
from .coordinator import BlitzerdeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.GEO_LOCATION,
]

_REFRESH_SCHEMA = vol.Schema(
    {vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string}
)


async def async_setup(
    hass: HomeAssistant, config: dict[str, Any]
) -> bool:
    """Set up global Blitzer.de services."""
    try:
        await async_register_card(hass)
    except Exception:  # pragma: no cover - frontend convenience must not block setup
        _LOGGER.exception("Could not register the Blitzer.de dashboard card")

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH,
            _async_handle_refresh,
            schema=_REFRESH_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up Blitzer.de from a config entry."""
    coordinator = BlitzerdeCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(
        entry.add_update_listener(_async_update_listener)
    )

    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )
    return True


async def _async_handle_refresh(
    call: ServiceCall,
) -> ServiceResponse:
    """Refresh one configured area immediately and return its current data."""
    hass = call.hass
    entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(
            f"'{entry_id}' is not a Blitzer.de config entry"
        )

    coordinator: BlitzerdeCoordinator = entry.runtime_data
    await coordinator.async_request_refresh()

    mapdata = coordinator.data.mapdata if coordinator.data else []
    return {
        "config_entry_id": entry.entry_id,
        "area": coordinator.displayname,
        "count": len(mapdata),
        "cameras": [
            {
                "backend": str(item.get("backend", "")).rsplit("-", 1)[-1],
                "vmax": item.get("vmax"),
                "city": (
                    item.get("address", {}).get("city")
                    if isinstance(item.get("address"), dict)
                    else None
                ),
                "street": (
                    item.get("address", {}).get("street")
                    if isinstance(item.get("address"), dict)
                    else None
                ),
                "latitude": item.get("lat"),
                "longitude": item.get("lng"),
                "distance_km": item.get("distance_km"),
            }
            for item in mapdata[: coordinator.sensorcount]
        ],
    }


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Reload the entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )


async def async_migrate_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Migrate older config entries to schema version 8."""
    if entry.version >= 8:
        return True

    _LOGGER.debug(
        "Migrating Blitzer.de config entry from version %s",
        entry.version,
    )

    data = dict(entry.data)
    data.setdefault(
        CONF_NAME,
        entry.title.removeprefix("Blitzer.de ") or "Home",
    )
    data.setdefault(CONF_COUNT, DEFAULT_SENSOR_COUNT)
    data.setdefault(CONF_TYPE, dict(DEFAULT_TYPES))
    data.setdefault(CONF_SELECTOR, DEFAULT_SELECTOR)
    data.setdefault(
        CONF_CONDITION, DEFAULT_ONLY_CONFIRMED
    )
    data.setdefault(
        CONF_UPDATE_INTERVAL,
        DEFAULT_UPDATE_INTERVAL_MINUTES,
    )
    data.setdefault(CONF_SEARCH_MODE, SEARCH_MODE_AREA)
    data.setdefault(CONF_NEW_MINUTES, DEFAULT_NEW_MINUTES)
    data.setdefault(CONF_BLACKLIST, DEFAULT_BLACKLIST)

    search_mode = data.get(CONF_SEARCH_MODE, SEARCH_MODE_AREA)
    if (
        search_mode == SEARCH_MODE_AREA
        and CONF_LOCATION not in data
    ):
        _LOGGER.error(
            "Cannot migrate area entry without a configured location"
        )
        return False
    if (
        search_mode != SEARCH_MODE_AREA
        and not data.get(CONF_WAYPOINTS)
    ):
        _LOGGER.error(
            "Cannot migrate route entry without configured waypoints"
        )
        return False

    hass.config_entries.async_update_entry(
        entry, data=data, version=8
    )
    _LOGGER.debug(
        "Blitzer.de config entry migration to version 8 completed"
    )
    return True
