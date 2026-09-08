"""Data update coordinator for Blitzer.de."""

from __future__ import annotations

import asyncio
import logging
import math
import re
from dataclasses import dataclass
from itertools import pairwise
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CONDITION,
    CONF_COUNT,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import APIConnectionError, APIRateLimitError, BlitzerdeAPI
from .const import (
    ATTR_DISTANCE_KM,
    CONF_CORRIDOR_WIDTH,
    CONF_SEARCH_MODE,
    CONF_UPDATE_INTERVAL,
    CONF_WAYPOINTS,
    DEFAULT_CORRIDOR_WIDTH_METERS,
    DEFAULT_ONLY_CONFIRMED,
    DEFAULT_SELECTOR,
    DEFAULT_SENSOR_COUNT,
    DEFAULT_TYPES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_ROUTE_QUERY_POINTS,
    SEARCH_MODE_AREA,
    SEARCH_MODE_ROUTE,
    TYPE_FIXED,
    TYPE_MOBILE,
    TYPE_TRAILER,
)
from .item_utils import item_info

_LOGGER = logging.getLogger(__name__)

_ROUTE_QUERY_CONCURRENCY = 5
_EARTH_RADIUS_M = 6_371_008.8


@dataclass(slots=True)
class BlitzerdeAPIData:
    """Normalized coordinator payload."""

    mapdata: list[dict[str, Any]]


class BlitzerdeCoordinator(DataUpdateCoordinator[BlitzerdeAPIData]):
    """Fetch and normalize Blitzer.de data for one config entry."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry
    ) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self.api = BlitzerdeAPI(hass)

        interval_minutes = int(
            config_entry.options.get(
                CONF_UPDATE_INTERVAL,
                config_entry.data.get(
                    CONF_UPDATE_INTERVAL,
                    DEFAULT_UPDATE_INTERVAL_MINUTES,
                ),
            )
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}:{config_entry.entry_id}",
            update_interval=(
                None
                if interval_minutes <= 0
                else timedelta(minutes=interval_minutes)
            ),
        )

    @property
    def displayname(self) -> str:
        """Return the configured display name."""
        return str(
            self.config_entry.data.get(
                CONF_NAME, self.config_entry.title
            )
        )

    @property
    def search_mode(self) -> str:
        """Return area or route search mode."""
        return str(
            self.config_entry.data.get(
                CONF_SEARCH_MODE, SEARCH_MODE_AREA
            )
        )

    @property
    def location(self) -> dict[str, Any]:
        """Return current area location options."""
        return dict(self._value(CONF_LOCATION, {}))

    @property
    def waypoints(self) -> list[dict[str, float]]:
        """Return configured route waypoints."""
        raw = self._value(CONF_WAYPOINTS, [])
        return [
            {
                "latitude": float(point["latitude"]),
                "longitude": float(point["longitude"]),
            }
            for point in raw
            if isinstance(point, dict)
            and "latitude" in point
            and "longitude" in point
        ]

    @property
    def corridor_width(self) -> float:
        """Return route corridor radius in meters."""
        return float(
            self._value(
                CONF_CORRIDOR_WIDTH,
                DEFAULT_CORRIDOR_WIDTH_METERS,
            )
        )

    @property
    def whitelist(self) -> str:
        """Return configured city regex."""
        return str(self._value(CONF_SELECTOR, DEFAULT_SELECTOR))

    @property
    def sensorcount(self) -> int:
        """Return configured number of binary/geolocation slots."""
        return int(self._value(CONF_COUNT, DEFAULT_SENSOR_COUNT))

    @property
    def update_interval_minutes(self) -> int:
        """Return the configured polling interval in minutes."""
        return int(
            self._value(
                CONF_UPDATE_INTERVAL,
                DEFAULT_UPDATE_INTERVAL_MINUTES,
            )
        )

    @property
    def types(self) -> dict[str, bool]:
        """Return enabled camera types."""
        raw = self._value(CONF_TYPE, DEFAULT_TYPES)
        return {
            key: bool(raw.get(key, default))
            for key, default in DEFAULT_TYPES.items()
        }

    @property
    def only_confirmed(self) -> bool:
        """Return whether only confirmed reports should be included."""
        return bool(
            self._value(
                CONF_CONDITION, DEFAULT_ONLY_CONFIRMED
            )
        )

    def _value(self, key: str, default: Any) -> Any:
        """Read an option first, then fall back to initial config data."""
        return self.config_entry.options.get(
            key, self.config_entry.data.get(key, default)
        )

    def enabled_types(self) -> list[int | str]:
        """Return the upstream type identifiers selected by the user."""
        selected: list[int | str] = []
        if self.types["mobile"]:
            selected.extend(TYPE_MOBILE)
        if self.types["trailer"]:
            selected.extend(TYPE_TRAILER)
        if self.types["fixed"]:
            selected.extend(TYPE_FIXED)
        return selected

    async def _async_update_data(self) -> BlitzerdeAPIData:
        """Fetch, filter and sort current camera data."""
        try:
            if self.search_mode == SEARCH_MODE_ROUTE:
                mapdata = await self._async_get_route_data()
            else:
                location = self.location
                mapdata = await self.api.async_get_area(
                    latitude=float(location["latitude"]),
                    longitude=float(location["longitude"]),
                    radius=float(location["radius"]),
                    types=self.enabled_types(),
                )
        except APIRateLimitError as err:
            raise UpdateFailed(
                retry_after=err.retry_after
            ) from err
        except (
            APIConnectionError,
            KeyError,
            TypeError,
            ValueError,
        ) as err:
            raise UpdateFailed(
                f"Error communicating with Blitzer.de: {err}"
            ) from err

        try:
            city_pattern = re.compile(self.whitelist)
        except re.error as err:
            raise UpdateFailed(
                f"Invalid city filter regular expression: {err}"
            ) from err

        filtered: list[dict[str, Any]] = []
        for item in mapdata:
            address = item.get("address")
            if not isinstance(address, dict):
                address = {}
            city = str(address.get("city") or "")
            if not city_pattern.search(city):
                continue

            if self.only_confirmed and not _is_confirmed(item):
                continue

            filtered.append(item)

        filtered.sort(
            key=lambda item: float(
                item.get(ATTR_DISTANCE_KM, math.inf)
            )
        )
        return BlitzerdeAPIData(mapdata=filtered)

    async def _async_get_route_data(self) -> list[dict[str, Any]]:
        """Search circles along the configured route and merge the results."""
        waypoints = self.waypoints
        if len(waypoints) < 2:
            raise ValueError("Route requires at least two waypoints")

        sample_points = _route_sample_points(
            waypoints, self.corridor_width
        )
        if len(sample_points) > MAX_ROUTE_QUERY_POINTS:
            raise ValueError(
                "Route requires too many upstream queries; "
                "increase corridor width or shorten the route"
            )

        merged: dict[str, dict[str, Any]] = {}
        types = self.enabled_types()

        for start in range(0, len(sample_points), _ROUTE_QUERY_CONCURRENCY):
            chunk = sample_points[
                start : start + _ROUTE_QUERY_CONCURRENCY
            ]
            responses = await asyncio.gather(
                *(
                    self.api.async_get_area(
                        latitude=latitude,
                        longitude=longitude,
                        radius=self.corridor_width,
                        types=types,
                    )
                    for latitude, longitude in chunk
                )
            )

            for items in responses:
                for raw_item in items:
                    backend = str(
                        raw_item.get("backend", "")
                    ).strip()
                    if not backend:
                        continue

                    item = dict(raw_item)
                    try:
                        item[ATTR_DISTANCE_KM] = round(
                            _distance_to_route_km(
                                float(item["lat"]),
                                float(item["lng"]),
                                waypoints,
                            ),
                            3,
                        )
                    except (KeyError, TypeError, ValueError):
                        continue

                    previous = merged.get(backend)
                    if previous is None or float(
                        item[ATTR_DISTANCE_KM]
                    ) < float(
                        previous.get(ATTR_DISTANCE_KM, math.inf)
                    ):
                        merged[backend] = item

        return sorted(
            merged.values(),
            key=lambda item: float(
                item.get(ATTR_DISTANCE_KM, math.inf)
            ),
        )


def _is_confirmed(item: dict[str, Any]) -> bool:
    """Treat permanent installations as confirmed even without a flag."""
    info = item_info(item)
    confirmed = info.get("confirmed")
    if confirmed is not None:
        return str(confirmed) == "1"

    code = str(item.get("type", ""))
    if str(info.get("fixed", "")) == "1":
        return True
    return code.isdigit() and 100 <= int(code) < 200


def _route_sample_points(
    waypoints: list[dict[str, float]],
    corridor_width_m: float,
) -> list[tuple[float, float]]:
    """Interpolate overlapping query centers along each route segment."""
    points: list[tuple[float, float]] = [
        (
            float(waypoints[0]["latitude"]),
            float(waypoints[0]["longitude"]),
        )
    ]

    for start, end in pairwise(waypoints):
        start_lat = float(start["latitude"])
        start_lng = float(start["longitude"])
        end_lat = float(end["latitude"])
        end_lng = float(end["longitude"])

        segment_m = _haversine_m(
            start_lat, start_lng, end_lat, end_lng
        )
        steps = max(
            1,
            math.ceil(
                segment_m / max(corridor_width_m, 1.0)
            ),
        )
        for step in range(1, steps + 1):
            fraction = step / steps
            points.append(
                (
                    start_lat
                    + (end_lat - start_lat) * fraction,
                    start_lng
                    + (end_lng - start_lng) * fraction,
                )
            )

    return points


def route_query_count(
    waypoints: list[dict[str, float]],
    corridor_width_m: float,
) -> int:
    """Return how many upstream circles a route needs."""
    if len(waypoints) < 2:
        return 0
    return len(
        _route_sample_points(
            waypoints, corridor_width_m
        )
    )


def _distance_to_route_km(
    latitude: float,
    longitude: float,
    waypoints: list[dict[str, float]],
) -> float:
    """Approximate shortest distance from a POI to the waypoint polyline."""
    distances = [
        _distance_point_to_segment_m(
            latitude,
            longitude,
            float(start["latitude"]),
            float(start["longitude"]),
            float(end["latitude"]),
            float(end["longitude"]),
        )
        for start, end in zip(waypoints, waypoints[1:])
    ]
    return min(distances) / 1000 if distances else math.inf


def _distance_point_to_segment_m(
    point_lat: float,
    point_lng: float,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
) -> float:
    """Distance to a short WGS84 segment using a local equirectangular plane."""
    reference_lat = math.radians(
        (point_lat + start_lat + end_lat) / 3
    )

    def xy(lat: float, lng: float) -> tuple[float, float]:
        return (
            math.radians(lng - point_lng)
            * _EARTH_RADIUS_M
            * math.cos(reference_lat),
            math.radians(lat - point_lat)
            * _EARTH_RADIUS_M,
        )

    sx, sy = xy(start_lat, start_lng)
    ex, ey = xy(end_lat, end_lng)
    dx = ex - sx
    dy = ey - sy
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(sx, sy)

    projection = max(
        0.0,
        min(1.0, -(sx * dx + sy * dy) / length_sq),
    )
    closest_x = sx + projection * dx
    closest_y = sy + projection * dy
    return math.hypot(closest_x, closest_y)


def _haversine_m(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """Return great-circle distance in meters."""
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
    return 2 * _EARTH_RADIUS_M * math.atan2(
        math.sqrt(a), math.sqrt(1 - a)
    )
