"""Contract tests for the traffic-digest blueprint."""

from pathlib import Path

ROOT_BLUEPRINT = Path("blueprints/automation/blitzerde/traffic_digest.yaml")
BUNDLED_BLUEPRINT = Path(
    "custom_components/blitzerde/blueprints/automation/blitzerde/traffic_digest.yaml"
)


def test_traffic_digest_blueprint_is_bundled_and_importable() -> None:
    """Keep the HACS-bundled and direct-import copies in lockstep."""
    assert ROOT_BLUEPRINT.is_file()
    assert BUNDLED_BLUEPRINT.is_file()
    assert ROOT_BLUEPRINT.read_text(encoding="utf-8") == BUNDLED_BLUEPRINT.read_text(
        encoding="utf-8"
    )


def test_traffic_digest_blueprint_closes_digest_feature_gap() -> None:
    """Protect the user-facing digest features from accidental regressions."""
    content = ROOT_BLUEPRINT.read_text(encoding="utf-8")

    for required in (
        "states.geo_location",
        "include_controls",
        "include_hazards",
        "include_archive",
        "max_distance_km",
        "max_reports",
        "platform: time",
        "platform: zone",
        "platform: state",
        "blitzerde_digest_requested",
        "persistent_notification.create",
        "delivery_actions",
        "sort(attribute='distance')",
    ):
        assert required in content

    # The digest is intentionally state-only: it must not add another upstream poll.
    assert "blitzerde.refresh" not in content
    assert "blitzerde.refresh_hazards" not in content


def test_traffic_digest_blueprint_preserves_three_language_support() -> None:
    """English, German, and Arabic remain first-class presentation choices."""
    content = ROOT_BLUEPRINT.read_text(encoding="utf-8")

    assert "value: en" in content
    assert "value: de" in content
    assert "value: ar" in content
    assert "Blitzer.de traffic digest" in content
    assert "Blitzer.de Verkehrslage" in content
    assert "ملخص Blitzer.de المروري" in content
