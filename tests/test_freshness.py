"""Tests for the pure report freshness helpers."""

from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "blitzerde"
    / "freshness.py"
)
SPEC = importlib.util.spec_from_file_location(
    "blitzerde_freshness", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
freshness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freshness)


class FreshnessTests(unittest.TestCase):
    """Validate the upstream timestamp formats we support."""

    def setUp(self) -> None:
        self.now = datetime(
            2026, 9, 8, 14, 30, tzinfo=timezone.utc
        )

    def test_same_day_time(self) -> None:
        self.assertEqual(
            freshness.minutes_since("14:00", self.now),
            30,
        )

    def test_time_ahead_rolls_to_yesterday(self) -> None:
        self.assertEqual(
            freshness.minutes_since("15:00", self.now),
            1410,
        )

    def test_calendar_date(self) -> None:
        self.assertEqual(
            freshness.minutes_since("07.09.2026", self.now),
            2310,
        )

    def test_invalid_value(self) -> None:
        self.assertIsNone(
            freshness.minutes_since("not-a-date", self.now)
        )

    def test_window(self) -> None:
        self.assertTrue(
            freshness.is_new_report("14:10", self.now, 60)
        )
        self.assertFalse(
            freshness.is_new_report("13:00", self.now, 60)
        )
        self.assertFalse(
            freshness.is_new_report("14:10", self.now, 0)
        )


if __name__ == "__main__":
    unittest.main()
