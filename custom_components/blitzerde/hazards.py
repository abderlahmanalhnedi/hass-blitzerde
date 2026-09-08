"""Normalization helpers for Blitzer.de traffic hazards.

This module intentionally keeps hazard semantics separate from controls.  The
upstream endpoint returns several shapes for hazard metadata, and Home
Assistant entities should not need to understand those quirks individually.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from .const import ATTR_DISTANCE_KM, HAZARD_CODE_KIND, HAZARD_ICONS
from .freshness import is_new_report, minutes_since


def hazard_kind(item: dict[str, Any]) -> str:
    """Return the semantic hazard kind represented by one upstream POI."""
    return HAZARD_CODE_KIND.get(str(item.get("type", "")), "unknown")


def hazard_info(item: dict[str, Any]) -> dict[str, Any]:
    """Return hazard ``info`` only when the upstream value is a mapping."""
    info = item.get("info")
    return info if isinstance(info, dict) else {}


def hazard_id(item: dict[str, Any]) -> str:
    """Return the public/stable-looking backend id for a hazard."""
    backend = str(item.get("backend", "")).strip()
    return backend.rsplit("-", 1)[-1] if backend else ""


def hazard_reason(item: dict[str, Any]) -> str:
    """Return the best available human-readable hazard description."""
    reason = item.get("reason")
    if reason not in (None, ""):
        return str(reason).strip()

    info = hazard_info(item)
    for key in ("reason", "desc", "description"):
        value = info.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def hazard_icon(item: dict[str, Any]) -> str:
    """Return an MDI icon for one semantic hazard kind."""
    return HAZARD_ICONS.get(hazard_kind(item), "mdi:alert")


def hazard_summary(item: dict[str, Any]) -> str:
    """Build a short automation/card-friendly summary for one hazard."""
    address = item.get("address")
    if not isinstance(address, dict):
        address = {}

    street = str(address.get("street") or "").strip()
    city = str(address.get("city") or "").strip()
    place = ", ".join(part for part in (street, city) if part)
    reason = hazard_reason(item)

    if reason and place:
        return f"{reason} · {place}"
    if reason:
        return reason
    if place:
        return place

    kind = hazard_kind(item).replace("_", " ").strip()
    return kind.title() if kind and kind != "unknown" else "Traffic hazard"


def normalize_hazards(
    items: Iterable[dict[str, Any]],
    *,
    enabled: Iterable[str],
    city_filter: str = ".*",
    blacklist_ids: Iterable[str] = (),
    new_minutes: int = 60,
    now: datetime,
) -> list[dict[str, Any]]:
    """Filter, normalize, deduplicate and distance-sort hazard POIs.

    The function is deliberately pure so coordinator code can share exactly
    the same behavior for radius searches, route corridors and future Drive
    Mode providers. Unknown upstream hazard types are ignored unless they are
    explicitly modelled in ``HAZARD_CODE_KIND``.
    """
    pattern = re.compile(city_filter)
    enabled_set = set(enabled)
    blacklist = {str(value).strip() for value in blacklist_ids if str(value).strip()}
    deduplicated: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []

    for raw in items:
        kind = hazard_kind(raw)
        if kind not in enabled_set:
            continue

        address = raw.get("address")
        if not isinstance(address, dict):
            address = {}
        city = str(address.get("city") or "")
        if not pattern.search(city):
            continue

        public_id = hazard_id(raw)
        backend = str(raw.get("backend", "")).strip()
        if public_id in blacklist or backend in blacklist:
            continue

        item = dict(raw)
        age = minutes_since(item.get("create_date"), now)
        if age is not None:
            item["age_minutes"] = age
        item["new"] = is_new_report(item.get("create_date"), now, new_minutes)
        item["hazard_kind"] = kind
        item["summary"] = hazard_summary(item)
        item["icon"] = hazard_icon(item)

        if public_id:
            previous = deduplicated.get(public_id)
            if previous is None or _distance(item) < _distance(previous):
                deduplicated[public_id] = item
        else:
            anonymous.append(item)

    result = [*deduplicated.values(), *anonymous]
    result.sort(key=_distance)
    return result


def _distance(item: dict[str, Any]) -> float:
    """Return a sortable distance, pushing missing/malformed values last."""
    try:
        return float(item.get(ATTR_DISTANCE_KM, math.inf))
    except (TypeError, ValueError):
        return math.inf
