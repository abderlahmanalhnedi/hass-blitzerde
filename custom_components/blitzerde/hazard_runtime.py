"""On-demand traffic-hazard runtime for Blitzer.de.

This is intentionally isolated from the camera coordinator. Hazard layers have
very different freshness characteristics and can be dense enough to consume a
shared upstream response budget. The service implemented here gives Home
Assistant automations a production-safe hazard path now, while the persistent
hazard coordinator can later reuse the same fetch helpers without coupling its
polling cadence to cameras.
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Iterable
from typing import Any

import voluptuous as vol
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HAZARD_BLACKLIST,
    CONF_HAZARD_COUNT,
    CONF_HAZARD_NEW_MINUTES,
    CONF_HAZARD_SELECTOR,
    CONF_HAZARDS,
    DEFAULT_HAZARD_COUNT,
    DEFAULT_NEW_MINUTES,
    DEFAULT_SELECTOR,
    DOMAIN,
    HAZARD_TYPES,
    MAX_SENSOR_COUNT,
    SEARCH_MODE_ROUTE,
    SERVICE_REFRESH_HAZARDS,
)
from .coordinator import BlitzerdeCoordinator
from .hazards import normalize_hazards
from .route import distance_to_route_km, route_sample_points

_HAZARD_QUERY_CONCURRENCY = 5

_REFRESH_HAZARDS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Optional("hazard_types"): vol.All(
            cv.ensure_list,
            [vol.In(tuple(HAZARD_TYPES))],
        ),
        vol.Optional("count"): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=MAX_SENSOR_COUNT),
        ),
    }
)


def _value(coordinator: BlitzerdeCoordinator, key: str, default: Any) -> Any:
    """Read a mutable option first, then initial config-entry data."""
    return coordinator.config_entry.options.get(
        key, coordinator.config_entry.data.get(key, default)
    )


def configured_hazard_types(coordinator: BlitzerdeCoordinator) -> list[str]:
    """Return enabled hazard kinds, falling back to all for legacy entries.

    Until the dedicated hazard options UI lands, entries created before hazard
    support have no hazard keys at all. Returning all kinds keeps the explicit
    on-demand action useful without changing their background polling behavior.
    Once an entry has a hazards mapping, that mapping is authoritative.
    """
    raw = _value(coordinator, CONF_HAZARDS, None)
    if raw is None:
        return list(HAZARD_TYPES)
    if not isinstance(raw, dict):
        return []
    return [kind for kind in HAZARD_TYPES if bool(raw.get(kind, False))]


def _csv_set(value: Any) -> set[str]:
    """Normalize comma/newline-separated IDs into a stable set."""
    return {
        part.strip()
        for part in str(value or "").replace("\n", ",").split(",")
        if part.strip()
    }


async def async_fetch_hazards(
    coordinator: BlitzerdeCoordinator,
    *,
    enabled: Iterable[str],
) -> list[dict[str, Any]]:
    """Fetch hazards for the entry's area or route without touching cameras."""
    enabled_types = [kind for kind in dict.fromkeys(enabled) if kind in HAZARD_TYPES]
    if not enabled_types:
        return []

    if coordinator.search_mode != SEARCH_MODE_ROUTE:
        location = coordinator.location
        return await coordinator.api.async_get_hazards(
            latitude=float(location["latitude"]),
            longitude=float(location["longitude"]),
            radius=float(location["radius"]),
            enabled=enabled_types,
        )

    waypoints = coordinator.waypoints
    sample_points = route_sample_points(waypoints, coordinator.corridor_width)
    merged: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []

    for start in range(0, len(sample_points), _HAZARD_QUERY_CONCURRENCY):
        chunk = sample_points[start : start + _HAZARD_QUERY_CONCURRENCY]
        responses = await asyncio.gather(
            *(
                coordinator.api.async_get_hazards(
                    latitude=latitude,
                    longitude=longitude,
                    radius=coordinator.corridor_width,
                    enabled=enabled_types,
                )
                for latitude, longitude in chunk
            )
        )

        for response in responses:
            for raw_item in response:
                item = dict(raw_item)
                try:
                    item["distance_km"] = round(
                        distance_to_route_km(
                            float(item["lat"]),
                            float(item["lng"]),
                            waypoints,
                        ),
                        3,
                    )
                except (KeyError, TypeError, ValueError):
                    continue

                backend = str(item.get("backend", "")).strip()
                if not backend:
                    anonymous.append(item)
                    continue

                previous = merged.get(backend)
                if previous is None or float(item["distance_km"]) < float(
                    previous.get("distance_km", math.inf)
                ):
                    merged[backend] = item

    result = [*merged.values(), *anonymous]
    result.sort(key=lambda item: float(item.get("distance_km", math.inf)))
    return result


async def _async_handle_refresh_hazards(call: ServiceCall) -> ServiceResponse:
    """Fetch traffic hazards independently and return normalized response data."""
    hass = call.hass
    entry_id = call.data[ATTR_CONFIG_ENTRY_ID]
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(
            f"'{entry_id}' is not a Blitzer.de config entry"
        )

    coordinator: BlitzerdeCoordinator = entry.runtime_data
    enabled = call.data.get("hazard_types") or configured_hazard_types(coordinator)
    raw = await async_fetch_hazards(coordinator, enabled=enabled)

    city_filter = str(_value(coordinator, CONF_HAZARD_SELECTOR, DEFAULT_SELECTOR))
    blacklist = _csv_set(_value(coordinator, CONF_HAZARD_BLACKLIST, ""))
    new_minutes = int(
        _value(coordinator, CONF_HAZARD_NEW_MINUTES, DEFAULT_NEW_MINUTES)
    )
    count = int(
        call.data.get(
            "count",
            _value(coordinator, CONF_HAZARD_COUNT, DEFAULT_HAZARD_COUNT),
        )
    )

    normalized = normalize_hazards(
        raw,
        enabled=enabled,
        city_filter=city_filter,
        blacklist_ids=blacklist,
        new_minutes=new_minutes,
        now=dt_util.now(),
    )[:count]

    return {
        "config_entry_id": entry.entry_id,
        "area": coordinator.displayname,
        "search_mode": coordinator.search_mode,
        "count": len(normalized),
        "hazards": [
            {
                "id": str(item.get("backend", "")).rsplit("-", 1)[-1],
                "hazard_kind": item.get("hazard_kind"),
                "summary": item.get("summary"),
                "city": (
                    item.get("address", {}).get("city")
                    if isinstance(item.get("address"), dict)
                    else None
                ),
                "street": (
                    item.get("address", {}).get("street")
                    if isinstance(item.get("address"), dict)
                    else None
                ),
                "latitude": item.get("lat"),
                "longitude": item.get("lng"),
                "distance_km": item.get("distance_km"),
                "new": item.get("new", False),
                "age_minutes": item.get("age_minutes"),
            }
            for item in normalized
        ],
    }


def async_register_hazard_services(hass: HomeAssistant) -> None:
    """Register the isolated hazard refresh action exactly once."""
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH_HAZARDS):
        return
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_HAZARDS,
        _async_handle_refresh_hazards,
        schema=_REFRESH_HAZARDS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
