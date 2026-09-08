"""Tests for semantic control taxonomy and archive handling."""

from __future__ import annotations

from custom_components.blitzerde.const import CODE_KIND, CONTROL_KINDS
from custom_components.blitzerde.coordinator import _is_confirmed
from custom_components.blitzerde.item_utils import (
    BlitzerItem,
    control_kind,
    is_archive,
)


def test_control_kind_mapping_is_complete_and_reversible() -> None:
    """Every configured raw code maps back to its declared semantic kind."""
    for kind, codes in CONTROL_KINDS.items():
        for code in codes:
            assert CODE_KIND[code] == kind
            assert control_kind({"type": code}) == kind


def test_unknown_control_kind_falls_back_safely() -> None:
    """Future upstream type codes are classified without crashing."""
    assert control_kind({"type": "999"}) == "unknown"
    assert control_kind({}) == "unknown"


def test_archive_detection_and_picture_path() -> None:
    """Archive records are explicit and use the upstream archive marker family."""
    speed = {"type": 201, "vmax": 80}
    distance = {"type": 206, "vmax": 100}

    assert is_archive(speed) is True
    assert is_archive(distance) is True
    assert is_archive({"type": 107}) is False
    assert BlitzerItem.get_picture_path(speed) == "mobile_archive_80"
    assert (
        BlitzerItem.get_picture_path(distance)
        == "mobile_archive_distance"
    )


def test_archive_is_not_hidden_by_confirmed_only() -> None:
    """Explicitly enabled historical records are not dropped for lacking flags."""
    assert _is_confirmed({"type": 201, "info": []}) is True
    assert _is_confirmed({"type": 206, "info": False}) is True


def test_attributes_expose_taxonomy_without_location_leak() -> None:
    """Entity attributes identify kind/archive state and keep location optional."""
    attrs = BlitzerItem.get_attributes(
        {
            "backend": "x-42",
            "type": 201,
            "vmax": 50,
            "lat": 51.0,
            "lng": 13.0,
            "address": {"city": "Dresden"},
        },
        include_location=False,
    )

    assert attrs["backend"] == "42"
    assert attrs["control_kind"] == "speed"
    assert attrs["archived"] is True
    assert attrs["type_code"] == "201"
    assert "latitude" not in attrs
    assert "longitude" not in attrs
