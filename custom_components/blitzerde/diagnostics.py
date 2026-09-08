"""Diagnostics support for Blitzer.de."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LOCATION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from .coordinator import BlitzerdeCoordinator

TO_REDACT = {CONF_LOCATION}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return privacy-conscious diagnostics for one config entry."""
    coordinator: BlitzerdeCoordinator = entry.runtime_data
    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": async_redact_data(
                dict(entry.data), TO_REDACT
            ),
            "options": async_redact_data(
                dict(entry.options), TO_REDACT
            ),
        },
        "coordinator": {
            "last_update_success": (
                coordinator.last_update_success
            ),
            "last_exception": (
                str(coordinator.last_exception)
                if coordinator.last_exception
                else None
            ),
            "detected_count": (
                len(coordinator.data.mapdata)
                if coordinator.data
                else 0
            ),
            "connected": coordinator.api.connected,
        },
    }
