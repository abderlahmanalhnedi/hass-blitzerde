"""Async API client for the unofficial Blitzer.de/atudo map endpoint."""

from __future__ import annotations

import asyncio
import json
import logging
import math
from collections.abc import Iterable, Sequence
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_TIMEOUT_SECONDS, API_URL, ATTR_DISTANCE_KM

_LOGGER = logging.getLogger(__name__)

JsonObject = dict[str, Any]


class BlitzerdeAPI:
    """Small, resilient client for the public map endpoint used by Blitzer.de."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the API client with an injected web session."""
        self._session = session
        self.connected = False

    async def _request_json(self, *, params: dict[str, str]) -> JsonObject:
        """Request JSON with timeout and useful error mapping."""
        try:
            async with asyncio.timeout(API_TIMEOUT_SECONDS):
                async with self._session.get(API_URL, params=params) as response:
                    if response.status == 429:
                        retry_after = _safe_retry_after(response.headers.get("Retry-After"))
                        raise APIRateLimitError(
                            "The upstream service rate-limited the request.",
                            retry_after=retry_after,
                        )
                    response.raise_for_status()
                    body = await response.text()
                    if not body.strip():
                        raise APIConnectionError(
                            "The upstream service returned an empty response."
                        )
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError as err:
                        raise APIConnectionError(
                            "The upstream service returned invalid JSON."
                        ) from err
        except APIRateLimitError:
            raise
        except TimeoutError as err:
            raise APIConnectionError("The upstream request timed out.") from err
        except ClientResponseError as err:
            raise APIConnectionError(
                f"The upstream service returned HTTP {err.status}."
            ) from err
        except ClientError as err:
            raise APIConnectionError(
                "Failed to connect to the upstream service."
            ) from err

        if not isinstance(data, dict):
            raise APIConnectionError("The upstream response has an unexpected format.")
        return data

    async def _request_pois(
        self,
        *,
        low_lat: float,
        low_lng: float,
        high_lat: float,
        high_lng: float,
        types: Sequence[int | str],
    ) -> list[JsonObject]:
        """Request POIs for a bounding box."""
        if not types:
            return []

        params = {
            "type": ",".join(map(str, types)),
            "box": (
                f"{low_lat:.7f},{low_lng:.7f},{high_lat:.7f},{high_lng:.7f}"
            ),
            "z": "18",
        }
        response_data = await self._request_json(params=params)
        pois = response_data.get("pois")
        if not isinstance(pois, list):
            raise APIConnectionError(
                "The upstream response does not contain a POI list."
            )

        self.connected = True
        return [item for item in pois if isinstance(item, dict)]

    async def async_get_area(
        self,
        *,
        latitude: float,
        longitude: float,
        radius: float,
        types: Sequence[int | str],
    ) -> list[JsonObject]:
        """Return deduplicated POIs inside the selected radius, nearest first."""
        radius_m = max(float(radius), 1.0)
        lat_delta, lng_delta = _radius_to_coordinate_delta(latitude, radius_m)

        areas = await self._request_pois(
            low_lat=latitude - lat_delta,
            low_lng=longitude - lng_delta,
            high_lat=latitude + lat_delta,
            high_lng=longitude + lng_delta,
            types=types,
        )

        areas = await self._resolve_clusters(
            areas,
            radius_m=radius_m,
            types=types,
            depth=0,
        )

        unique_items: dict[str, JsonObject] = {}
        anonymous_items: list[JsonObject] = []
        for item in areas:
            if item.get("type") == "cluster":
                continue
            try:
                item_lat = float(item["lat"])
                item_lng = float(item["lng"])
            except (KeyError, TypeError, ValueError):
                _LOGGER.debug("Ignoring POI with invalid coordinates: %s", item)
                continue

            distance_km = _haversine_km(
                latitude, longitude, item_lat, item_lng
            )
            if distance_km * 1000 > radius_m:
                continue

            normalized = dict(item)
            normalized[ATTR_DISTANCE_KM] = round(distance_km, 3)
            backend = str(item.get("backend", "")).strip()
            if backend:
                unique_items[backend] = normalized
            else:
                anonymous_items.append(normalized)

        result = [*unique_items.values(), *anonymous_items]
        result.sort(
            key=lambda item: float(item.get(ATTR_DISTANCE_KM, math.inf))
        )
        return result

    async def async_test_connection(
        self,
        *,
        latitude: float,
        longitude: float,
        radius: float,
        types: Sequence[int | str],
    ) -> None:
        """Validate that the upstream endpoint is reachable and returns valid data."""
        await self.async_get_area(
            latitude=latitude,
            longitude=longitude,
            radius=min(max(float(radius), 250.0), 2000.0),
            types=types,
        )

    async def _resolve_clusters(
        self,
        areas: Iterable[JsonObject],
        *,
        radius_m: float,
        types: Sequence[int | str],
        depth: int,
    ) -> list[JsonObject]:
        """Resolve the occasional cluster without allowing unbounded recursion."""
        resolved: list[JsonObject] = []
        for area in areas:
            if area.get("type") != "cluster":
                resolved.append(area)
                continue

            if depth >= 3 or radius_m <= 25:
                _LOGGER.debug(
                    "Skipping unresolved cluster at recursion depth %s", depth
                )
                continue

            try:
                lat = float(area["lat"])
                lng = float(area["lng"])
            except (KeyError, TypeError, ValueError):
                continue

            child_radius = max(radius_m / 10, 25.0)
            lat_delta, lng_delta = _radius_to_coordinate_delta(
                lat, child_radius
            )
            children = await self._request_pois(
                low_lat=lat - lat_delta,
                low_lng=lng - lng_delta,
                high_lat=lat + lat_delta,
                high_lng=lng + lng_delta,
                types=types,
            )
            resolved.extend(
                await self._resolve_clusters(
                    children,
                    radius_m=child_radius,
                    types=types,
                    depth=depth + 1,
                )
            )
        return resolved


class APIConnectionError(Exception):
    """Raised when the upstream service cannot be used."""


class APIRateLimitError(APIConnectionError):
    """Raised when the upstream service asks us to back off."""

    def __init__(self, message: str, *, retry_after: float = 60.0) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def _safe_retry_after(value: str | None) -> float:
    """Return a bounded Retry-After value."""
    try:
        seconds = float(value) if value is not None else 60.0
    except ValueError:
        seconds = 60.0
    return min(max(seconds, 30.0), 3600.0)


def _radius_to_coordinate_delta(
    latitude: float, radius_m: float
) -> tuple[float, float]:
    """Convert radius in meters to an approximate latitude/longitude delta."""
    lat_delta = radius_m / 111_320.0
    cos_lat = max(abs(math.cos(math.radians(latitude))), 0.01)
    lng_delta = radius_m / (111_320.0 * cos_lat)
    return lat_delta, lng_delta


def _haversine_km(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """Calculate great-circle distance between two WGS84 coordinates."""
    earth_radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * earth_radius_km * math.atan2(
        math.sqrt(a), math.sqrt(1 - a)
    )
