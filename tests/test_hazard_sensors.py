"""Tests for traffic-hazard summary sensors."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.blitzerde.const import (
    CONF_HAZARDS,
    HAZARD_DEFAULTS,
)
from custom_components.blitzerde.hazard_coordinator import BlitzerdeHazardCoordinator
from custom_components.blitzerde.sensor import (
    BlitzerHazardCountSensor,
    BlitzerNearestHazardSensor,
    BlitzerNewHazardCountSensor,
)


def _coordinator(hass) -> BlitzerdeHazardCoordinator:
    hazards = dict(HAZARD_DEFAULTS)
    hazards["accident"] = True
    hazards["roadwork_temporary"] = True
    camera = SimpleNamespace(
        config_entry=SimpleNamespace(
            entry_id="hazard-sensor-test",
            data={CONF_HAZARDS: hazards},
            options={},
        ),
        displayname="Dresden",
    )
    coordinator = BlitzerdeHazardCoordinator(hass, camera)
    coordinator.data = [
        {
            "backend": "21-42",
            "hazard_kind": "accident",
            "summary": "Accident · B170, Dresden",
            "distance_km": 0.4,
            "lat": 51.05,
            "lng": 13.74,
            "address": {"city": "Dresden", "street": "B170"},
            "new": True,
            "age_minutes": 5,
        },
        {
            "backend": "22-99",
            "hazard_kind": "roadwork_temporary",
            "summary": "Roadwork · A4, Dresden",
            "distance_km": 1.8,
            "lat": 51.08,
            "lng": 13.70,
            "address": {"city": "Dresden", "street": "A4"},
            "new": False,
            "age_minutes": 90,
        },
    ]
    return coordinator


def test_hazard_count_sensor_exposes_dashboard_aggregates(hass) -> None:
    """Hazard totals stay on the independent coordinator data channel."""
    coordinator = _coordinator(hass)
    entry = SimpleNamespace(entry_id="hazard-sensor-test")
    sensor = BlitzerHazardCountSensor(coordinator, entry)

    assert sensor.native_value == 2
    assert sensor.extra_state_attributes["by_kind"] == {
        "accident": 1,
        "roadwork_temporary": 1,
    }
    assert sensor.extra_state_attributes["enabled_types"] == [
        "accident",
        "roadwork_temporary",
    ]
    assert sensor.extra_state_attributes["background_polling"] is False


def test_nearest_hazard_sensor_exposes_normalized_details(hass) -> None:
    """The nearest hazard sensor is automation-friendly without raw API parsing."""
    coordinator = _coordinator(hass)
    entry = SimpleNamespace(entry_id="hazard-sensor-test")
    sensor = BlitzerNearestHazardSensor(coordinator, entry)

    assert sensor.native_value == 0.4
    assert sensor.extra_state_attributes == {
        "hazard_kind": "accident",
        "summary": "Accident · B170, Dresden",
        "city": "Dresden",
        "street": "B170",
        "latitude": 51.05,
        "longitude": 13.74,
        "new": True,
        "age_minutes": 5,
        "config_entry_id": "hazard-sensor-test",
    }


def test_new_hazard_sensor_counts_fresh_items(hass) -> None:
    """Fresh hazards get their own count instead of sharing camera state."""
    coordinator = _coordinator(hass)
    entry = SimpleNamespace(entry_id="hazard-sensor-test")
    sensor = BlitzerNewHazardCountSensor(coordinator, entry)

    assert sensor.native_value == 1


def test_nearest_hazard_sensor_handles_empty_and_malformed_distance(hass) -> None:
    """Missing or malformed distances never break the sensor platform."""
    coordinator = _coordinator(hass)
    entry = SimpleNamespace(entry_id="hazard-sensor-test")
    sensor = BlitzerNearestHazardSensor(coordinator, entry)

    coordinator.data = []
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}

    coordinator.data = [{"distance_km": "not-a-number"}]
    assert sensor.native_value is None
