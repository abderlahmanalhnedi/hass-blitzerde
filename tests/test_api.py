"""Tests for the Home Assistant-independent Blitzer.de API client."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.blitzerde.api import (
    APIConnectionError,
    APIRateLimitError,
    BlitzerdeAPI,
    _haversine_km,
    _radius_to_coordinate_delta,
    _safe_retry_after,
)


class FakeResponse:
    """Minimal aiohttp response double."""

    def __init__(
        self,
        *,
        status: int = 200,
        body: str = '{"pois": []}',
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self) -> None:
        if self.status >= 400:
            from aiohttp import ClientResponseError

            raise ClientResponseError(
                request_info=None,
                history=(),
                status=self.status,
                message="failure",
                headers=self.headers,
            )

    async def text(self) -> str:
        return self._body


class FakeSession:
    """Minimal ClientSession double returning a configured response."""

    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get(self, url: str, *, params: dict[str, str]):
        self.calls.append((url, params))
        return self.response


async def test_request_json_success() -> None:
    """A valid JSON mapping is returned unchanged."""
    session = FakeSession(
        FakeResponse(body='{"pois": [{"backend": "1-42"}]}')
    )
    api = BlitzerdeAPI(session)  # type: ignore[arg-type]

    data = await api._request_json(params={"type": "0"})

    assert data["pois"][0]["backend"] == "1-42"
    assert session.calls


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("", "empty response"),
        ("not-json", "invalid JSON"),
        ("[]", "unexpected format"),
    ],
)
async def test_request_json_rejects_bad_payloads(
    body: str, message: str
) -> None:
    """Malformed upstream responses become stable integration errors."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(FakeResponse(body=body))
    )

    with pytest.raises(APIConnectionError, match=message):
        await api._request_json(params={"type": "0"})


async def test_rate_limit_honors_retry_after() -> None:
    """HTTP 429 exposes a bounded Retry-After value to the coordinator."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(
            FakeResponse(
                status=429,
                headers={"Retry-After": "120"},
            )
        )
    )

    with pytest.raises(APIRateLimitError) as err:
        await api._request_json(params={"type": "0"})

    assert err.value.retry_after == 120


async def test_http_error_is_mapped() -> None:
    """HTTP failures are converted to APIConnectionError."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(FakeResponse(status=503))
    )

    with pytest.raises(APIConnectionError, match="HTTP 503"):
        await api._request_json(params={"type": "0"})


async def test_request_pois_requires_list() -> None:
    """The POI endpoint must return a list under the pois key."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(FakeResponse(body='{"pois": false}'))
    )

    with pytest.raises(APIConnectionError, match="POI list"):
        await api._request_pois(
            low_lat=51.0,
            low_lng=13.0,
            high_lat=52.0,
            high_lng=14.0,
            types=[0],
        )


async def test_request_pois_skips_network_when_no_types() -> None:
    """No selected upstream types produces no request."""
    session = FakeSession(FakeResponse())
    api = BlitzerdeAPI(session)  # type: ignore[arg-type]

    assert (
        await api._request_pois(
            low_lat=51.0,
            low_lng=13.0,
            high_lat=52.0,
            high_lng=14.0,
            types=[],
        )
        == []
    )
    assert session.calls == []


async def test_area_filters_radius_coordinates_and_duplicates() -> None:
    """Area lookup keeps valid unique in-radius POIs and sorts by distance."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(FakeResponse())
    )
    api._request_pois = AsyncMock(
        return_value=[
            {
                "backend": "1-near",
                "lat": 51.0505,
                "lng": 13.7373,
                "type": 0,
            },
            {
                "backend": "1-near",
                "lat": 51.0506,
                "lng": 13.7373,
                "type": 0,
            },
            {
                "backend": "1-far",
                "lat": 52.0,
                "lng": 13.7373,
                "type": 0,
            },
            {
                "backend": "broken",
                "lat": "bad",
                "lng": 13.7,
                "type": 0,
            },
            {
                "lat": 51.0507,
                "lng": 13.7373,
                "type": 0,
            },
        ]
    )

    result = await api.async_get_area(
        latitude=51.0504,
        longitude=13.7373,
        radius=1000,
        types=[0],
    )

    assert len(result) == 2
    assert result[0]["backend"] == "1-near"
    assert "distance_km" in result[0]
    assert "backend" not in result[1]
    assert all(item.get("backend") != "1-far" for item in result)


async def test_cluster_resolution_recurses_and_stops() -> None:
    """Cluster resolution queries children without allowing endless recursion."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(FakeResponse())
    )
    api._request_pois = AsyncMock(
        return_value=[
            {
                "backend": "1-child",
                "lat": 51.0505,
                "lng": 13.7373,
                "type": 0,
            }
        ]
    )

    resolved = await api._resolve_clusters(
        [
            {
                "type": "cluster",
                "lat": 51.05,
                "lng": 13.73,
            }
        ],
        radius_m=1000,
        types=[0],
        depth=0,
    )
    assert resolved[0]["backend"] == "1-child"

    unresolved = await api._resolve_clusters(
        [
            {
                "type": "cluster",
                "lat": 51.05,
                "lng": 13.73,
            }
        ],
        radius_m=1000,
        types=[0],
        depth=3,
    )
    assert unresolved == []


async def test_cluster_with_invalid_coordinates_is_ignored() -> None:
    """A malformed cluster never breaks an update."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(FakeResponse())
    )

    resolved = await api._resolve_clusters(
        [{"type": "cluster", "lat": "bad", "lng": 13.7}],
        radius_m=1000,
        types=[0],
        depth=0,
    )

    assert resolved == []


async def test_connection_test_bounds_probe_radius() -> None:
    """Connection tests avoid issuing an unnecessarily huge probe."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(FakeResponse())
    )
    api.async_get_area = AsyncMock(return_value=[])

    await api.async_test_connection(
        latitude=51.0,
        longitude=13.0,
        radius=50_000,
        types=[0],
    )

    assert api.async_get_area.await_args.kwargs["radius"] == 2000.0


def test_retry_after_is_safely_bounded() -> None:
    """Retry-After parsing has useful minimum and maximum bounds."""
    assert _safe_retry_after(None) == 60
    assert _safe_retry_after("invalid") == 60
    assert _safe_retry_after("1") == 30
    assert _safe_retry_after("99999") == 3600


def test_geometry_helpers() -> None:
    """Pure coordinate helpers behave sensibly."""
    lat_delta, lng_delta = _radius_to_coordinate_delta(
        51.0, 1000
    )
    assert lat_delta > 0
    assert lng_delta > lat_delta
    assert _haversine_km(51.0, 13.0, 51.0, 13.0) == 0


async def test_timeout_is_mapped() -> None:
    """A timeout becomes a stable APIConnectionError."""

    class TimeoutContext:
        async def __aenter__(self):
            raise TimeoutError

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class TimeoutSession:
        def get(self, url: str, *, params: dict[str, str]):
            return TimeoutContext()

    api = BlitzerdeAPI(TimeoutSession())  # type: ignore[arg-type]

    with pytest.raises(APIConnectionError, match="timed out"):
        await api._request_json(params={"type": "0"})


async def test_client_error_is_mapped() -> None:
    """Low-level aiohttp client failures become APIConnectionError."""
    from aiohttp import ClientError

    class ClientErrorContext:
        async def __aenter__(self):
            raise ClientError("network down")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class ClientErrorSession:
        def get(self, url: str, *, params: dict[str, str]):
            return ClientErrorContext()

    api = BlitzerdeAPI(ClientErrorSession())  # type: ignore[arg-type]

    with pytest.raises(APIConnectionError, match="Failed to connect"):
        await api._request_json(params={"type": "0"})


async def test_request_pois_sets_connected_and_filters_non_objects() -> None:
    """Successful POI requests mark the client connected and keep mappings only."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(
            FakeResponse(
                body='{"pois": [{"backend": "1-42"}, false, "bad"]}'
            )
        )
    )

    pois = await api._request_pois(
        low_lat=51.0,
        low_lng=13.0,
        high_lat=52.0,
        high_lng=14.0,
        types=[0],
    )

    assert api.connected is True
    assert pois == [{"backend": "1-42"}]


async def test_area_ignores_cluster_left_after_resolution() -> None:
    """A defensive leftover cluster is never exposed as a camera."""
    api = BlitzerdeAPI(  # type: ignore[arg-type]
        FakeSession(FakeResponse())
    )
    api._request_pois = AsyncMock(return_value=[])
    api._resolve_clusters = AsyncMock(
        return_value=[
            {
                "type": "cluster",
                "lat": 51.05,
                "lng": 13.73,
            },
            {
                "backend": "1-42",
                "type": 0,
                "lat": 51.0505,
                "lng": 13.7373,
            },
        ]
    )

    result = await api.async_get_area(
        latitude=51.0504,
        longitude=13.7373,
        radius=1000,
        types=[0],
    )

    assert [item["backend"] for item in result] == ["1-42"]
