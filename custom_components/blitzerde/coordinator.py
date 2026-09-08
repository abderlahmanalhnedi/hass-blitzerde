"""Data update coordinator for Blitzer.de."""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
from dataclasses import dataclass
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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
    async_create_issue,
    async_delete_issue,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import APIConnectionError, APIRateLimitError, BlitzerdeAPI
from .const import (
    ATTR_DISTANCE_KM,
    CODE_KIND,
    CONF_BLACKLIST,
    CONF_CORRIDOR_WIDTH,
    CONF_KINDS,
    CONF_NEW_MINUTES,
    CONF_SEARCH_MODE,
    CONF_UPDATE_INTERVAL,
    CONF_WAYPOINTS,
    DEFAULT_BLACKLIST,
    DEFAULT_CORRIDOR_WIDTH_METERS,
    DEFAULT_NEW_MINUTES,
    DEFAULT_ONLY_CONFIRMED,
    DEFAULT_SELECTOR,
    KIND_DEFAULTS,
    DEFAULT_SENSOR_COUNT,
    DEFAULT_TYPES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_ROUTE_QUERY_POINTS,
    REPAIR_UPSTREAM_UNAVAILABLE,
    SEARCH_MODE_AREA,
    SEARCH_MODE_ROUTE,
    TYPE_ARCHIVE,
    TYPE_FIXED,
    TYPE_MOBILE,
    TYPE_TRAILER,
    UPSTREAM_REPAIR_FAILURE_THRESHOLD,
)
from .freshness import is_new_report, minutes_since
from .item_utils import item_info
from .route import distance_to_route_km, route_sample_points

_LOGGER = logging.getLogger(__name__)

_ROUTE_QUERY_CONCURRENCY = 5


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
        self.api = BlitzerdeAPI(async_get_clientsession(hass))
        self.last_successful_update = None
        self.last_update_duration_ms: int | None = None
        self.consecutive_failures = 0
        self._repair_issue_id = (
            f"{REPAIR_UPSTREAM_UNAVAILABLE}_{config_entry.entry_id}"
        )

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
    def new_minutes(self) -> int:
        """Return how long a report counts as new."""
        return int(
            self._value(
                CONF_NEW_MINUTES,
                DEFAULT_NEW_MINUTES,
            )
        )

    @property
    def blacklist_ids(self) -> set[str]:
        """Return ignored public or full backend camera IDs."""
        raw = str(
            self._value(
                CONF_BLACKLIST,
                DEFAULT_BLACKLIST,
            )
        )
        return {
            part.strip()
            for part in raw.replace("\n", ",").split(",")
            if part.strip()
        }

    @property
    def new_count(self) -> int:
        """Return how many currently filtered reports are marked new."""
        if not self.data:
            return 0
        return sum(
            1
            for item in self.data.mapdata
            if item.get("new") is True
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
    def kinds(self) -> dict[str, bool]:
        """Return enabled semantic control kinds."""
        raw = self._value(CONF_KINDS, KIND_DEFAULTS)
        return {
            key: bool(raw.get(key, default))
            for key, default in KIND_DEFAULTS.items()
        }

    def _kind_enabled(self, item: dict[str, Any]) -> bool:
        """Return whether the arriving POI matches the selected kind filter."""
        kind = CODE_KIND.get(str(item.get("type", "")), "unknown")
        return self.kinds.get(kind, False)

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
        if self.types.get("archive", False):
            selected.extend(TYPE_ARCHIVE)
        return selected

    async def _async_update_data(self) -> BlitzerdeAPIData:
        """Fetch, filter and sort current camera data."""
        started = time.perf_counter()
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
            self._record_failure(started)
            raise UpdateFailed(
                retry_after=err.retry_after
            ) from err
        except (
            APIConnectionError,
            KeyError,
            TypeError,
            ValueError,
        ) as err:
            self._record_failure(started)
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
        blacklist_ids = self.blacklist_ids
        now = dt_util.now()
        for item in mapdata:
            address = item.get("address")
            if not isinstance(address, dict):
                address = {}
            city = str(address.get("city") or "")
            if not city_pattern.search(city):
                continue

            backend = str(item.get("backend", "")).strip()
            public_id = backend.rsplit("-", 1)[-1] if backend else ""
            if (
                backend in blacklist_ids
                or public_id in blacklist_ids
            ):
                continue

            if not self._kind_enabled(item):
                continue

            if self.only_confirmed and not _is_confirmed(item):
                continue

            normalized = dict(item)
            age_minutes = minutes_since(
                normalized.get("create_date"),
                now,
            )
            if age_minutes is not None:
                normalized["age_minutes"] = age_minutes
            normalized["new"] = is_new_report(
                normalized.get("create_date"),
                now,
                self.new_minutes,
            )
            filtered.append(normalized)

        filtered.sort(
            key=lambda item: float(
                item.get(ATTR_DISTANCE_KM, math.inf)
            )
        )
        self._record_success(started)
        return BlitzerdeAPIData(mapdata=filtered)

    def _record_failure(self, started: float) -> None:
        """Record a failed refresh and surface persistent trouble via Repairs."""
        self.consecutive_failures += 1
        self.last_update_duration_ms = round(
            (time.perf_counter() - started) * 1000
        )

        if (
            self.consecutive_failures
            != UPSTREAM_REPAIR_FAILURE_THRESHOLD
        ):
            return

        async_create_issue(
            self.hass,
            DOMAIN,
            self._repair_issue_id,
            is_fixable=False,
            is_persistent=False,
            severity=IssueSeverity.WARNING,
            translation_key=REPAIR_UPSTREAM_UNAVAILABLE,
            translation_placeholders={
                "name": self.displayname,
                "failures": str(self.consecutive_failures),
            },
            learn_more_url=(
                "https://github.com/abderlahmanalhnedi/"
                "hass-blitzerde#troubleshooting"
            ),
        )

    def _record_success(self, started: float) -> None:
        """Record a successful refresh and clear any upstream repair issue."""
        self.last_update_duration_ms = round(
            (time.perf_counter() - started) * 1000
        )
        self.last_successful_update = dt_util.now()
        self.consecutive_failures = 0
        async_delete_issue(
            self.hass,
            DOMAIN,
            self._repair_issue_id,
        )

    async def _async_get_route_data(self) -> list[dict[str, Any]]:
        """Search circles along the configured route and merge the results."""
        waypoints = self.waypoints
        if len(waypoints) < 2:
            raise ValueError("Route requires at least two waypoints")

        sample_points = route_sample_points(
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
                            distance_to_route_km(
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
    if code.isdigit() and 200 <= int(code) < 300:
        return True
    return code.isdigit() and 100 <= int(code) < 200
