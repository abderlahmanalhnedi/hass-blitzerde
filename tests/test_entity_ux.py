"""Real-device UX regression tests for Blitzer.de entities."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.blitzerde.binary_sensor import _camera_slot_assigned
from custom_components.blitzerde.sensor import (
    _camera_display_name,
    _hazard_channel_enabled,
    _latest_camera_item,
)


def test_latest_camera_prefers_lowest_normalized_age() -> None:
    """Latest camera follows report freshness, not the largest backend ID."""
    older = {
        "backend": "mobile-999",
        "age_minutes": 45,
        "address": {"street": "Older Straße", "city": "Dresden"},
    }
    newer = {
        "backend": "mobile-100",
        "age_minutes": 3,
        "address": {"street": "Neue Straße", "city": "Dresden"},
    }

    assert _latest_camera_item([older, newer]) is newer


def test_latest_camera_label_prefers_street_and_city() -> None:
    """The state shown on the device page should be meaningful to humans."""
    item = {
        "backend": "mobile-266684203",
        "address": {"street": "Hepkestraße", "city": "Dresden"},
    }

    assert _camera_display_name(item) == "Hepkestraße, Dresden"


def test_latest_camera_label_has_safe_fallbacks() -> None:
    """Sparse upstream payloads still produce a stable readable state."""
    assert (
        _camera_display_name(
            {
                "backend": "mobile-42",
                "info": {"desc": "Mobile control"},
            }
        )
        == "Mobile control"
    )
    assert _camera_display_name({"backend": "mobile-42"}) == "Camera 42"


def test_empty_camera_slots_are_not_reported_safe() -> None:
    """Configured capacity beyond current results must become unavailable."""
    coordinator = SimpleNamespace(
        data=SimpleNamespace(mapdata=[{"backend": "one"}])
    )

    assert _camera_slot_assigned(coordinator, 0) is True
    assert _camera_slot_assigned(coordinator, 1) is False


def test_hazard_channel_availability_tracks_configuration() -> None:
    """Disabled hazard monitoring must not imply that the road is hazard-free."""
    assert _hazard_channel_enabled([]) is False
    assert _hazard_channel_enabled(["accident"]) is True
