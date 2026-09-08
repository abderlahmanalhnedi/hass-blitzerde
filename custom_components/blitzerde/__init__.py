"""Blitzer.de custom integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CONDITION,
    CONF_COUNT,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_TYPE,
    Platform,
)
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_ONLY_CONFIRMED,
    DEFAULT_SELECTOR,
    DEFAULT_SENSOR_COUNT,
    DEFAULT_TYPES,
)
from .coordinator import BlitzerdeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


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
    """Migrate older config entries to schema version 5."""
    if entry.version >= 5:
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

    if CONF_LOCATION not in data:
        _LOGGER.error(
            "Cannot migrate Blitzer.de entry without a configured location"
        )
        return False

    hass.config_entries.async_update_entry(
        entry, data=data, version=5
    )
    _LOGGER.debug(
        "Blitzer.de config entry migration to version 5 completed"
    )
    return True
