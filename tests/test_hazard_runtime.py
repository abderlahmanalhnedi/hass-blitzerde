"""Tests for the isolated traffic-hazard runtime."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.blitzerde.const import HAZARD_TYPES, SEARCH_MODE_AREA
from custom_components.blitzerde.hazard_runtime import (
    async_fetch_hazards,
    configured_hazard_types,
)


def _coordinator(*, data=None, options=None, api=None):
    return SimpleNamespace(
        config_entry=SimpleNamespace(data=data or {}, options=options or {}),
        search_mode=SEARCH_MODE_AREA,
        location={"latitude": 51.05, "longitude": 13.74, "radius": 1500},
        api=api,
    )


def test_legacy_entries_get_all_hazards_for_explicit_action() -> None:
    """Entries without hazard config remain useful for manual scans."""
    coordinator = _coordinator()

    assert configured_hazard_types(coordinator) == list(HAZARD_TYPES)


def test_configured_hazards_are_authoritative() -> None:
    """Once a hazards mapping exists, only explicitly enabled kinds are used."""
    coordinator = _coordinator(
        data={
            "hazards": {
                "accident": True,
                "closure": True,
                "tailback_end": False,
            }
        }
    )

    assert configured_hazard_types(coordinator) == ["accident", "closure"]


def test_options_override_initial_hazard_config() -> None:
    """Mutable options take precedence over initial config-entry data."""
    coordinator = _coordinator(
        data={"hazards": {"accident": True}},
        options={"hazards": {"roadwork_temporary": True}},
    )

    assert configured_hazard_types(coordinator) == ["roadwork_temporary"]


@pytest.mark.asyncio
async def test_area_hazard_fetch_is_isolated_from_control_api() -> None:
    """Area scans call the dedicated hazard endpoint helper with selected kinds."""
    api = SimpleNamespace(
        async_get_hazards=AsyncMock(
            return_value=[
                {
                    "backend": "20-123",
                    "type": "20",
                    "lat": 51.051,
                    "lng": 13.741,
                    "distance_km": 0.2,
                }
            ]
        )
    )
    coordinator = _coordinator(api=api)

    result = await async_fetch_hazards(
        coordinator,
        enabled=["tailback_end", "not-a-real-kind", "tailback_end"],
    )

    assert result[0]["backend"] == "20-123"
    api.async_get_hazards.assert_awaited_once_with(
        latitude=51.05,
        longitude=13.74,
        radius=1500.0,
        enabled=["tailback_end"],
    )


@pytest.mark.asyncio
async def test_no_enabled_hazards_makes_no_request() -> None:
    """An empty selection never consumes upstream request budget."""
    api = SimpleNamespace(async_get_hazards=AsyncMock())
    coordinator = _coordinator(api=api)

    assert await async_fetch_hazards(coordinator, enabled=[]) == []
    api.async_get_hazards.assert_not_awaited()
