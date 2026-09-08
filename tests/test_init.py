"""Runtime setup tests for the Blitzer.de integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_LOCATION, CONF_NAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.blitzerde import (
    PLATFORMS,
    async_migrate_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.blitzerde.const import (
    CONF_BLACKLIST,
    CONF_NEW_MINUTES,
    CONF_SEARCH_MODE,
    DEFAULT_BLACKLIST,
    DEFAULT_NEW_MINUTES,
    DOMAIN,
    SEARCH_MODE_AREA,
    SEARCH_MODE_ROUTE,
    SERVICE_REFRESH,
)

AREA_LOCATION = {
    "latitude": 51.0504,
    "longitude": 13.7373,
    "radius": 1500,
}


async def test_async_setup_registers_service(hass) -> None:
    """Global setup registers the refresh action and bundled card."""
    with patch(
        "custom_components.blitzerde.async_register_card",
        new_callable=AsyncMock,
    ) as register_card:
        assert await async_setup(hass, {}) is True

    register_card.assert_awaited_once_with(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_REFRESH)


async def test_setup_entry_uses_runtime_data(hass) -> None:
    """A config entry stores its coordinator in ConfigEntry.runtime_data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        data={
            CONF_NAME: "Dresden",
            CONF_SEARCH_MODE: SEARCH_MODE_AREA,
            CONF_LOCATION: AREA_LOCATION,
        },
    )
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with (
        patch(
            "custom_components.blitzerde.BlitzerdeCoordinator",
            return_value=coordinator,
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(),
        ) as forward_setups,
    ):
        assert await async_setup_entry(hass, entry) is True

    coordinator.async_config_entry_first_refresh.assert_awaited_once()
    assert entry.runtime_data is coordinator
    forward_setups.assert_awaited_once_with(entry, PLATFORMS)


async def test_unload_entry_unloads_platforms(hass) -> None:
    """Unload delegates all platform cleanup to Home Assistant."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        data={CONF_LOCATION: AREA_LOCATION},
    )
    entry.add_to_hass(hass)

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new=AsyncMock(return_value=True),
    ) as unload_platforms:
        assert await async_unload_entry(hass, entry) is True

    unload_platforms.assert_awaited_once_with(entry, PLATFORMS)


async def test_migrate_area_entry(hass) -> None:
    """Older area entries receive current defaults safely."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        version=6,
        data={CONF_LOCATION: AREA_LOCATION},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.version == 8
    assert entry.data[CONF_SEARCH_MODE] == SEARCH_MODE_AREA
    assert entry.data[CONF_NEW_MINUTES] == DEFAULT_NEW_MINUTES
    assert entry.data[CONF_BLACKLIST] == DEFAULT_BLACKLIST


async def test_migrate_area_without_location_fails(hass) -> None:
    """An invalid historical area is not silently migrated."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Broken",
        version=6,
        data={},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False
    assert entry.version == 6


async def test_migrate_route_without_waypoints_fails(hass) -> None:
    """An invalid historical route is not silently migrated."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Broken route",
        version=7,
        data={CONF_SEARCH_MODE: SEARCH_MODE_ROUTE},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False
    assert entry.version == 7
