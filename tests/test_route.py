"""Tests for the pure route geometry helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "blitzerde"
    / "route.py"
)
SPEC = importlib.util.spec_from_file_location(
    "blitzerde_route", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
route = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(route)


class RouteTests(unittest.TestCase):
    """Validate route geometry independently of Home Assistant."""

    def setUp(self) -> None:
        self.waypoints = [
            {"latitude": 51.05, "longitude": 13.73},
            {"latitude": 51.05, "longitude": 13.75},
        ]

    def test_query_count_grows_when_corridor_is_narrower(self) -> None:
        wide = route.route_query_count(
            self.waypoints, 1000
        )
        narrow = route.route_query_count(
            self.waypoints, 250
        )
        self.assertGreater(narrow, wide)

    def test_distance_on_route_is_near_zero(self) -> None:
        distance = route.distance_to_route_km(
            51.05,
            13.74,
            self.waypoints,
        )
        self.assertLess(distance, 0.01)

    def test_distance_off_route_is_positive(self) -> None:
        distance = route.distance_to_route_km(
            51.06,
            13.74,
            self.waypoints,
        )
        self.assertGreater(distance, 1.0)

    def test_sample_contains_endpoints(self) -> None:
        points = route.route_sample_points(
            self.waypoints, 500
        )
        self.assertEqual(
            points[0],
            (51.05, 13.73),
        )
        self.assertAlmostEqual(
            points[-1][0], 51.05, places=6
        )
        self.assertAlmostEqual(
            points[-1][1], 13.75, places=6
        )


if __name__ == "__main__":
    unittest.main()
