"""Runtime tests for the resilient Blitzer.de API adapter."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.blitzerde.api import (
    APIConnectionError,
    APIRateLimitError,
    BlitzerdeAPI,
    _safe_retry_after,
)
from custom_components.blitzerde.const import API_URL, ATTR_DISTANCE_KM

pytestmark = pytest.mark.asyncio


async def test_request_json_success(hass, aioclient_mock: Any) -> None:
    """Test a successful JSON response."""
    session = aioclient_mock.create_session(hass.loop)
    aioclient_mock.get(
        API_URL,
        params={"probe": "1"},
        json={"pois": []},
    )

    api = BlitzerdeAPI(hass, session)
    assert await api._request_json(
        params={"probe": "1"}
    ) == {"pois": []}


async def test_request_json_rate_limit(hass, aioclient_mock: Any) -> None:
    """Test HTTP 429 becomes a bounded retry-aware exception."""
    session = aioclient_mock.create_session(hass.loop)
    aioclient_mock.get(
        API_URL,
        params={"probe": "1"},
        status=429,
        headers={"Retry-After": "120"},
    )

    api = BlitzerdeAPI(hass, session)
    with pytest.raises(APIRateLimitError) as exc:
        await api._request_json(params={"probe": "1"})

    assert exc.value.retry_after == 120


async def test_request_json_rejects_invalid_payload(
    hass, aioclient_mock: Any
) -> None:
    """Test malformed and structurally invalid upstream data fail safely."""
    session = aioclient_mock.create_session(hass.loop)
    aioclient_mock.get(
        API_URL,
        params={"probe": "bad-json"},
        text="{broken",
    )
    api = BlitzerdeAPI(hass, session)

    with pytest.raises(
        APIConnectionError, match="invalid JSON"
    ):
        await api._request_json(
            params={"probe": "bad-json"}
        )

    aioclient_mock.get(
        API_URL,
        params={"probe": "wrong-shape"},
        json=["not", "an", "object"],
    )
    with pytest.raises(
        APIConnectionError, match="unexpected format"
    ):
        await api._request_json(
            params={"probe": "wrong-shape"}
        )


async def test_request_pois_validates_list(
    hass, aioclient_mock: Any
) -> None:
    """Test POI responses require a list and discard non-object entries."""
    session = aioclient_mock.create_session(hass.loop)
    api = BlitzerdeAPI(hass, session)

    with patch.object(
        api,
        "_request_json",
        AsyncMock(return_value={"pois": "wrong"}),
    ):
        with pytest.raises(
            APIConnectionError, match="POI list"
        ):
            await api._request_pois(
                low_lat=1,
                low_lng=2,
                high_lat=3,
                high_lng=4,
                types=[1],
            )

    with patch.object(
        api,
        "_request_json",
        AsyncMock(
            return_value={
                "pois": [
                    {"backend": "a"},
                    False,
                    [],
                    {"backend": "b"},
                ]
            }
        ),
    ):
        result = await api._request_pois(
            low_lat=1,
            low_lng=2,
            high_lat=3,
            high_lng=4,
            types=[1],
        )

    assert result == [
        {"backend": "a"},
        {"backend": "b"},
    ]
    assert api.connected is True


async def test_area_filters_radius_deduplicates_and_sorts(hass) -> None:
    """Test the area result is circular, deduplicated and nearest-first."""
    api = BlitzerdeAPI(hass)
    raw = [
        {
            "backend": "same",
            "lat": 51.0510,
            "lng": 13.7373,
        },
        {
            "backend": "farther",
            "lat": 51.0520,
            "lng": 13.7373,
        },
        {
            "backend": "same",
            "lat": 51.0505,
            "lng": 13.7373,
        },
        {
            "backend": "outside",
            "lat": 51.1000,
            "lng": 13.7373,
        },
        {
            "backend": "invalid",
            "lat": "not-a-number",
            "lng": 13.7373,
        },
    ]

    with (
        patch.object(
            api,
            "_request_pois",
            AsyncMock(return_value=raw),
        ),
        patch.object(
            api,
            "_resolve_clusters",
            AsyncMock(return_value=raw),
        ),
    ):
        result = await api.async_get_area(
            latitude=51.0504,
            longitude=13.7373,
            radius=1000,
            types=[1],
        )

    assert [item["backend"] for item in result] == [
        "same",
        "farther",
    ]
    assert result[0][ATTR_DISTANCE_KM] < result[1][ATTR_DISTANCE_KM]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, 60.0),
        ("not-a-number", 60.0),
        ("1", 30.0),
        ("120", 120.0),
        ("99999", 3600.0),
    ],
)
async def test_retry_after_is_bounded(
    raw: str | None, expected: float
) -> None:
    """Test Retry-After cannot force unreasonable retry windows."""
    assert _safe_retry_after(raw) == expected
