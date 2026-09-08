"""Home Assistant runtime tests for Blitzer.de."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import (
    CONF_CONDITION,
    CONF_COUNT,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_TYPE,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry


from custom_components.blitzerde.const import (
    CONF_BLACKLIST,
    CONF_NEW_MINUTES,
    CONF_SEARCH_MODE,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    SEARCH_MODE_AREA,
    UPSTREAM_REPAIR_FAILURE_THRESHOLD,
)
from custom_components.blitzerde.coordinator import BlitzerdeCoordinator

pytestmark = pytest.mark.asyncio

ENTRY_DATA = {
    CONF_NAME: "Dresden",
    CONF_SEARCH_MODE: SEARCH_MODE_AREA,
    CONF_LOCATION: {
        "latitude": 51.0504,
        "longitude": 13.7373,
        "radius": 1500,
    },
    CONF_TYPE: {
        "mobile": True,
        "trailer": True,
        "fixed": False,
    },
    CONF_COUNT: 9,
    CONF_SELECTOR: ".*",
    CONF_CONDITION: True,
    CONF_UPDATE_INTERVAL: 1,
    CONF_NEW_MINUTES: 60,
    CONF_BLACKLIST: "",
}


async def test_setup_and_unload_entry(hass) -> None:
    """Test a complete config-entry setup without real network access."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        unique_id="dresden",
        data=ENTRY_DATA,
        version=8,
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.blitzerde.async_register_card",
            AsyncMock(return_value=None),
        ),
        patch(
            "custom_components.blitzerde.api.BlitzerdeAPI.async_get_area",
            AsyncMock(return_value=[]),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert isinstance(entry.runtime_data, BlitzerdeCoordinator)
    assert entry.runtime_data.last_update_success is True

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_migrate_legacy_area_entry(hass) -> None:
    """Test older entries get all modern defaults without losing location."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Legacy",
        data={
            CONF_NAME: "Legacy",
            CONF_LOCATION: ENTRY_DATA[CONF_LOCATION],
        },
        version=5,
    )
    entry.add_to_hass(hass)

    from custom_components.blitzerde import async_migrate_entry

    assert await async_migrate_entry(hass, entry)
    assert entry.version == 8
    assert entry.data[CONF_SEARCH_MODE] == SEARCH_MODE_AREA
    assert entry.data[CONF_NEW_MINUTES] == 60
    assert entry.data[CONF_BLACKLIST] == ""


async def test_repair_issue_after_repeated_failures(hass) -> None:
    """Test repeated upstream failures create and recovery clears a repair."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        data=ENTRY_DATA,
        version=8,
    )
    coordinator = BlitzerdeCoordinator(hass, entry)

    with (
        patch(
            "custom_components.blitzerde.coordinator.async_create_issue"
        ) as create_issue,
        patch(
            "custom_components.blitzerde.coordinator.async_delete_issue"
        ) as delete_issue,
    ):
        for _ in range(UPSTREAM_REPAIR_FAILURE_THRESHOLD - 1):
            coordinator._record_failure(time.perf_counter())
        create_issue.assert_not_called()

        coordinator._record_failure(time.perf_counter())
        create_issue.assert_called_once()
        assert coordinator.consecutive_failures == (
            UPSTREAM_REPAIR_FAILURE_THRESHOLD
        )

        coordinator._record_success(time.perf_counter())
        delete_issue.assert_called_once()
        assert coordinator.consecutive_failures == 0
        assert coordinator.last_successful_update is not None
