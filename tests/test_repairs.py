"""Tests for Home Assistant Repairs integration."""

from __future__ import annotations

import time
from unittest.mock import patch

from homeassistant.const import (
    CONF_CONDITION,
    CONF_COUNT,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_TYPE,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.blitzerde import async_remove_entry
from custom_components.blitzerde.const import (
    CONF_BLACKLIST,
    CONF_NEW_MINUTES,
    CONF_SEARCH_MODE,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    REPAIR_UPSTREAM_UNAVAILABLE,
    SEARCH_MODE_AREA,
    UPSTREAM_REPAIR_FAILURE_THRESHOLD,
)
from custom_components.blitzerde.coordinator import BlitzerdeCoordinator

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


async def test_repair_created_after_repeated_failures_and_cleared(hass) -> None:
    """Persistent upstream failures create one warning which recovery clears."""
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

        # Further failures do not keep recreating the same issue.
        coordinator._record_failure(time.perf_counter())
        create_issue.assert_called_once()

        coordinator._record_success(time.perf_counter())
        delete_issue.assert_called_once()
        assert coordinator.consecutive_failures == 0
        assert coordinator.last_successful_update is not None


async def test_remove_entry_cleans_repair_issue(hass) -> None:
    """Deleting a config entry removes any repair issue owned by it."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        data=ENTRY_DATA,
        version=8,
    )

    with patch(
        "custom_components.blitzerde.async_delete_issue"
    ) as delete_issue:
        await async_remove_entry(hass, entry)

    delete_issue.assert_called_once_with(
        hass,
        DOMAIN,
        f"{REPAIR_UPSTREAM_UNAVAILABLE}_{entry.entry_id}",
    )
