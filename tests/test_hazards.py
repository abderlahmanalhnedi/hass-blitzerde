"""Tests for hazard normalization helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.blitzerde.hazards import (
    hazard_id,
    hazard_info,
    hazard_kind,
    hazard_reason,
    hazard_summary,
    normalize_hazards,
)


def _now() -> datetime:
    return datetime(2026, 9, 9, 1, 30, tzinfo=UTC)


def test_hazard_helpers_tolerate_real_upstream_shapes() -> None:
    item = {
        "backend": "20-12345",
        "type": "20",
        "reason": "Queue end",
        "info": False,
        "address": {"street": "A4", "city": "Dresden"},
    }

    assert hazard_kind(item) == "tailback_end"
    assert hazard_id(item) == "12345"
    assert hazard_info(item) == {}
    assert hazard_reason(item) == "Queue end"
    assert hazard_summary(item) == "Queue end · A4, Dresden"


def test_reason_falls_back_to_info_mapping() -> None:
    assert (
        hazard_reason({"info": {"desc": "Object on road"}})
        == "Object on road"
    )


def test_normalize_filters_deduplicates_and_sorts() -> None:
    items = [
        {
            "backend": "21-2",
            "type": "21",
            "lat": 51.0,
            "lng": 13.7,
            "distance_km": 2.4,
            "create_date": "01:10",
            "address": {"city": "Dresden", "street": "B170"},
        },
        {
            "backend": "20-1",
            "type": "20",
            "lat": 51.1,
            "lng": 13.8,
            "distance_km": 0.8,
            "create_date": "01:20",
            "reason": "Slow traffic",
            "address": {"city": "Dresden"},
        },
        {
            "backend": "20-1",
            "type": "20",
            "lat": 51.1,
            "lng": 13.8,
            "distance_km": 1.1,
            "create_date": "01:20",
            "address": {"city": "Dresden"},
        },
        {
            "backend": "23-9",
            "type": "23",
            "distance_km": 0.2,
            "create_date": "01:25",
            "address": {"city": "Leipzig"},
        },
    ]

    result = normalize_hazards(
        items,
        enabled={"tailback_end", "accident", "obstacle"},
        city_filter="^Dresden$",
        now=_now(),
        new_minutes=30,
    )

    assert [hazard_id(item) for item in result] == ["1", "2"]
    assert result[0]["distance_km"] == 0.8
    assert result[0]["hazard_kind"] == "tailback_end"
    assert result[0]["new"] is True
    assert result[0]["age_minutes"] == 10
    assert result[1]["age_minutes"] == 20


def test_normalize_supports_public_and_full_backend_blacklists() -> None:
    items = [
        {"backend": "20-1", "type": "20", "distance_km": 1},
        {"backend": "21-2", "type": "21", "distance_km": 2},
        {"backend": "22-3", "type": "22", "distance_km": 3},
    ]

    result = normalize_hazards(
        items,
        enabled={"tailback_end", "accident", "roadwork_temporary"},
        blacklist_ids={"1", "21-2"},
        now=_now(),
    )

    assert [hazard_id(item) for item in result] == ["3"]


def test_unknown_and_disabled_hazards_do_not_leak() -> None:
    items = [
        {"backend": "x-1", "type": "999", "distance_km": 0.1},
        {"backend": "21-2", "type": "21", "distance_km": 0.2},
    ]

    result = normalize_hazards(
        items,
        enabled={"tailback_end"},
        now=_now(),
    )

    assert result == []


def test_missing_distance_is_sorted_last_without_crashing() -> None:
    items = [
        {"backend": "20-1", "type": "20", "distance_km": "bad"},
        {"backend": "20-2", "type": "20", "distance_km": 0.5},
    ]

    result = normalize_hazards(
        items,
        enabled={"tailback_end"},
        now=_now(),
    )

    assert [hazard_id(item) for item in result] == ["2", "1"]
