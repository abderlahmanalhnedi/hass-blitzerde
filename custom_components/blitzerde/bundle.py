"""Serve the Blitzer.de dashboard card bundled with the integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_CARD_FILE = "blitzerde-card.js"
_CARD_URL_BASE = f"/{DOMAIN}_static"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve and register the bundled Lovelace card."""
    source = Path(__file__).parent / "frontend" / _CARD_FILE
    url = f"{_CARD_URL_BASE}/{_CARD_FILE}"

    await hass.http.async_register_static_paths(
        [StaticPathConfig(url, str(source), False)]
    )

    integration = await async_get_integration(hass, DOMAIN)
    add_extra_js_url(
        hass, f"{url}?v={integration.version}"
    )
