"""Tests for the traffic-hazard foundation."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.blitzerde.api import BlitzerdeAPI
from custom_components.blitzerde.const import (
    HAZARD_CODE_KIND,
    HAZARD_DEFAULTS,
    HAZARD_ICONS,
    HAZARD_TYPES,
)


def test_hazard_taxonomy_is_complete_and_opt_in() -> None:
    """Every supported hazard has a reversible code, icon and safe default."""
    assert len(HAZARD_TYPES) == 10
    assert set(HAZARD_DEFAULTS) == set(HAZARD_TYPES)
    assert set(HAZARD_ICONS) == set(HAZARD_TYPES)
    assert all(enabled is False for enabled in HAZARD_DEFAULTS.values())

    for kind, code in HAZARD_TYPES.items():
        assert HAZARD_CODE_KIND[code] == kind


@pytest.mark.asyncio
async def test_hazard_query_uses_only_enabled_semantic_types() -> None:
    """Hazard polling stays isolated and ignores unknown persisted options."""
    api = BlitzerdeAPI(AsyncMock())
    api.async_get_area = AsyncMock(return_value=[{"backend": "h-1"}])

    result = await api.async_get_hazards(
        latitude=51.05,
        longitude=13.74,
        radius=2500,
        enabled=["accident", "unknown_future_key", "closure", "accident"],
    )

    assert result == [{"backend": "h-1"}]
    api.async_get_area.assert_awaited_once_with(
        latitude=51.05,
        longitude=13.74,
        radius=2500,
        types=(HAZARD_TYPES["accident"], HAZARD_TYPES["closure"]),
    )


@pytest.mark.asyncio
async def test_hazard_query_short_circuits_when_disabled() -> None:
    """No upstream request is spent when the user has enabled no hazards."""
    api = BlitzerdeAPI(AsyncMock())
    api.async_get_area = AsyncMock()

    result = await api.async_get_hazards(
        latitude=51.05,
        longitude=13.74,
        radius=2500,
        enabled=[],
    )

    assert result == []
    api.async_get_area.assert_not_awaited()
