"""Home Assistant coordinator tests for Blitzer.de."""

from __future__ import annotations

from datetime import UTC, datetime
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
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.blitzerde.api import (
    APIConnectionError,
    APIRateLimitError,
)
from custom_components.blitzerde.const import (
    ATTR_DISTANCE_KM,
    CONF_BLACKLIST,
    CONF_CORRIDOR_WIDTH,
    CONF_NEW_MINUTES,
    CONF_SEARCH_MODE,
    CONF_UPDATE_INTERVAL,
    CONF_WAYPOINTS,
    DOMAIN,
    SEARCH_MODE_AREA,
    SEARCH_MODE_ROUTE,
)
from custom_components.blitzerde.coordinator import (
    BlitzerdeAPIData,
    BlitzerdeCoordinator,
)

AREA_LOCATION = {
    "latitude": 51.0504,
    "longitude": 13.7373,
    "radius": 2500,
}
TYPES = {
    "mobile": True,
    "trailer": False,
    "fixed": True,
}


def _entry(
    hass,
    *,
    mode: str = SEARCH_MODE_AREA,
    options: dict | None = None,
    **extra,
):
    data = {
        CONF_NAME: "Dresden",
        CONF_SEARCH_MODE: mode,
        CONF_LOCATION: AREA_LOCATION,
        CONF_TYPE: TYPES,
        CONF_COUNT: 9,
        CONF_SELECTOR: "^Dresden$",
        CONF_CONDITION: True,
        CONF_UPDATE_INTERVAL: 1,
        CONF_NEW_MINUTES: 60,
        CONF_BLACKLIST: "99",
        **extra,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        data=data,
        options=options or {},
    )
    entry.add_to_hass(hass)
    return entry


async def test_properties_and_options_override(hass) -> None:
    """Coordinator properties prefer mutable ConfigEntry.options."""
    entry = _entry(
        hass,
        options={
            CONF_COUNT: 12,
            CONF_UPDATE_INTERVAL: 0,
            CONF_BLACKLIST: "1, 2\n3",
        },
    )
    coordinator = BlitzerdeCoordinator(hass, entry)

    assert coordinator.displayname == "Dresden"
    assert coordinator.search_mode == SEARCH_MODE_AREA
    assert coordinator.location == AREA_LOCATION
    assert coordinator.sensorcount == 12
    assert coordinator.update_interval_minutes == 0
    assert coordinator.blacklist_ids == {"1", "2", "3"}
    assert coordinator.update_interval is None
    assert 0 in coordinator.enabled_types()
    assert 101 in coordinator.enabled_types()
    assert "ts" not in coordinator.enabled_types()
    assert coordinator.new_count == 0

    coordinator.data = BlitzerdeAPIData(
        mapdata=[
            {"new": True},
            {"new": False},
            {"new": True},
        ]
    )
    assert coordinator.new_count == 2


async def test_area_update_filters_and_marks_freshness(hass) -> None:
    """Area updates apply city, blacklist, confirmation and freshness filters."""
    entry = _entry(hass)
    coordinator = BlitzerdeCoordinator(hass, entry)
    coordinator.api.async_get_area = AsyncMock(
        return_value=[
            {
                "backend": "1-42",
                "lat": 51.05,
                "lng": 13.74,
                ATTR_DISTANCE_KM: 0.5,
                "address": {"city": "Dresden"},
                "info": {"confirmed": "1"},
                "create_date": "14:10",
            },
            {
                "backend": "1-99",
                "lat": 51.05,
                "lng": 13.74,
                ATTR_DISTANCE_KM: 0.2,
                "address": {"city": "Dresden"},
                "info": {"confirmed": "1"},
                "create_date": "14:20",
            },
            {
                "backend": "1-43",
                "lat": 51.05,
                "lng": 13.74,
                ATTR_DISTANCE_KM: 0.1,
                "address": {"city": "Leipzig"},
                "info": {"confirmed": "1"},
                "create_date": "14:20",
            },
            {
                "backend": "1-44",
                "lat": 51.05,
                "lng": 13.74,
                ATTR_DISTANCE_KM: 0.3,
                "address": {"city": "Dresden"},
                "info": {"confirmed": "0"},
                "create_date": "14:20",
            },
        ]
    )
    now = datetime(2026, 9, 8, 14, 30, tzinfo=UTC)

    with patch(
        "custom_components.blitzerde.coordinator.dt_util.now",
        return_value=now,
    ):
        result = await coordinator._async_update_data()

    assert [item["backend"] for item in result.mapdata] == ["1-42"]
    assert result.mapdata[0]["age_minutes"] == 20
    assert result.mapdata[0]["new"] is True
    assert coordinator.last_successful_update == now
    assert coordinator.consecutive_failures == 0
    assert coordinator.last_update_duration_ms is not None


@pytest.mark.parametrize(
    "error",
    [
        APIConnectionError("offline"),
        KeyError("latitude"),
        ValueError("bad coordinate"),
    ],
)
async def test_area_update_maps_failures(hass, error: Exception) -> None:
    """Expected upstream/config errors become UpdateFailed."""
    entry = _entry(hass)
    coordinator = BlitzerdeCoordinator(hass, entry)
    coordinator.api.async_get_area = AsyncMock(
        side_effect=error
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.consecutive_failures == 1
    assert coordinator.last_update_duration_ms is not None


async def test_rate_limit_preserves_retry_after(hass) -> None:
    """Coordinator propagates upstream backoff to Home Assistant."""
    entry = _entry(hass)
    coordinator = BlitzerdeCoordinator(hass, entry)
    coordinator.api.async_get_area = AsyncMock(
        side_effect=APIRateLimitError(
            "rate limited", retry_after=180
        )
    )

    with pytest.raises(UpdateFailed) as err:
        await coordinator._async_update_data()

    assert err.value.retry_after == 180
    assert coordinator.consecutive_failures == 1


async def test_invalid_city_regex_is_update_failure(hass) -> None:
    """A corrupted persisted regex cannot crash the coordinator."""
    entry = _entry(
        hass,
        options={CONF_SELECTOR: "["},
    )
    coordinator = BlitzerdeCoordinator(hass, entry)
    coordinator.api.async_get_area = AsyncMock(return_value=[])

    with pytest.raises(UpdateFailed, match="regular expression"):
        await coordinator._async_update_data()


async def test_route_requires_two_waypoints(hass) -> None:
    """A broken route entry fails safely."""
    entry = _entry(
        hass,
        mode=SEARCH_MODE_ROUTE,
        **{
            CONF_WAYPOINTS: [
                {"latitude": 51.05, "longitude": 13.73}
            ],
            CONF_CORRIDOR_WIDTH: 500,
        },
    )
    coordinator = BlitzerdeCoordinator(hass, entry)

    with pytest.raises(UpdateFailed, match="two waypoints"):
        await coordinator._async_update_data()


async def test_route_queries_merge_and_deduplicate(hass) -> None:
    """Route lookup merges overlapping query circles by backend ID."""
    waypoints = [
        {"latitude": 51.05, "longitude": 13.73},
        {"latitude": 51.05, "longitude": 13.75},
    ]
    entry = _entry(
        hass,
        mode=SEARCH_MODE_ROUTE,
        options={CONF_CONDITION: False},
        **{
            CONF_WAYPOINTS: waypoints,
            CONF_CORRIDOR_WIDTH: 500,
        },
    )
    coordinator = BlitzerdeCoordinator(hass, entry)

    coordinator.api.async_get_area = AsyncMock(
        side_effect=[
            [
                {
                    "backend": "1-42",
                    "lat": 51.0501,
                    "lng": 13.74,
                    "address": {"city": "Dresden"},
                },
                {
                    "backend": "",
                    "lat": 51.05,
                    "lng": 13.74,
                },
                {
                    "backend": "broken",
                    "lat": "bad",
                    "lng": 13.74,
                },
            ],
            [
                {
                    "backend": "1-42",
                    "lat": 51.05,
                    "lng": 13.74,
                    "address": {"city": "Dresden"},
                },
                {
                    "backend": "1-43",
                    "lat": 51.0502,
                    "lng": 13.745,
                    "address": {"city": "Dresden"},
                },
            ],
        ]
    )

    with patch(
        "custom_components.blitzerde.coordinator.route_sample_points",
        return_value=[
            (51.05, 13.73),
            (51.05, 13.75),
        ],
    ):
        result = await coordinator._async_get_route_data()

    assert {item["backend"] for item in result} == {
        "1-42",
        "1-43",
    }
    assert len(
        [
            item
            for item in result
            if item["backend"] == "1-42"
        ]
    ) == 1
    assert all(ATTR_DISTANCE_KM in item for item in result)


async def test_route_query_budget_is_enforced(hass) -> None:
    """An unexpectedly huge route is rejected before API requests."""
    waypoints = [
        {"latitude": 51.05, "longitude": 13.73},
        {"latitude": 53.55, "longitude": 9.99},
    ]
    entry = _entry(
        hass,
        mode=SEARCH_MODE_ROUTE,
        **{
            CONF_WAYPOINTS: waypoints,
            CONF_CORRIDOR_WIDTH: 100,
        },
    )
    coordinator = BlitzerdeCoordinator(hass, entry)

    with pytest.raises(
        ValueError, match="too many upstream queries"
    ):
        await coordinator._async_get_route_data()


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        ({"info": {"confirmed": "1"}}, True),
        ({"info": {"confirmed": "0"}}, False),
        ({"info": {"fixed": "1"}}, True),
        ({"type": 101}, True),
        ({"type": 0}, False),
    ],
)
def test_confirmation_rules(item: dict, expected: bool) -> None:
    """Permanent installations remain visible without community flags."""
    from custom_components.blitzerde.coordinator import _is_confirmed

    assert _is_confirmed(item) is expected
