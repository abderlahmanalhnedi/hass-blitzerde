"""Tests for the independent traffic-hazard coordinator."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.blitzerde.hazard_coordinator import BlitzerdeHazardCoordinator


@pytest.mark.asyncio
async def test_hazard_coordinator_persists_normalized_results(hass) -> None:
    """A refresh stores normalized hazards for map entities and events."""
    config_entry = SimpleNamespace(
        entry_id="hazard-test",
        data={},
        options={},
    )
    camera = SimpleNamespace(
        config_entry=config_entry,
        displayname="Dresden",
    )
    coordinator = BlitzerdeHazardCoordinator(hass, camera)

    raw = [
        {
            "backend": "21-42",
            "type": "21",
            "lat": 51.05,
            "lng": 13.74,
            "distance_km": 0.4,
            "address": {"city": "Dresden", "street": "B170"},
        }
    ]

    with patch(
        "custom_components.blitzerde.hazard_coordinator.async_fetch_hazards",
        AsyncMock(return_value=raw),
    ):
        result = await coordinator._async_update_data()

    assert len(result) == 1
    assert result[0]["hazard_kind"] == "accident"
    assert result[0]["backend"] == "21-42"


def test_hazard_coordinator_is_manual_only_by_default(hass) -> None:
    """Creating the hazard channel never silently adds background requests."""
    camera = SimpleNamespace(
        config_entry=SimpleNamespace(entry_id="hazard-test", data={}, options={}),
        displayname="Dresden",
    )

    coordinator = BlitzerdeHazardCoordinator(hass, camera)

    assert coordinator.update_interval is None
