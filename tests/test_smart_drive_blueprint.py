"""Contract tests for the Smart Drive Alerts blueprint."""

from pathlib import Path


BLUEPRINT = (
    Path(__file__).parents[1]
    / "custom_components"
    / "blitzerde"
    / "blueprints"
    / "automation"
    / "blitzerde"
    / "smart_drive_alerts.yaml"
)


def _text() -> str:
    return BLUEPRINT.read_text(encoding="utf-8")


def test_blueprint_ships_inside_integration_package() -> None:
    """Keep the blueprint in the HACS-installed custom component tree."""
    assert BLUEPRINT.is_file()
    assert "custom_components/blitzerde/blueprints/" in str(BLUEPRINT)


def test_blueprint_listens_to_both_new_report_events() -> None:
    """One automation should cover controls and traffic hazards."""
    text = _text()
    assert "event_type: blitzerde_new_camera" in text
    assert "event_type: blitzerde_new_hazard" in text


def test_blueprint_has_smart_drive_safety_filters() -> None:
    """Protect the distance, urgency and quiet-hours behaviour."""
    text = _text()
    for contract in (
        "critical_distance:",
        "max_distance:",
        "control_kinds:",
        "hazard_types:",
        "min_vmax:",
        "quiet_from:",
        "quiet_to:",
        "is_critical:",
        "urgency:",
    ):
        assert contract in text


def test_blueprint_keeps_tri_lingual_labels() -> None:
    """English, German and Arabic remain visible in the blueprint UI."""
    text = _text()
    assert "Scope / Bereich / النطاق" in text
    assert "Hazard filters / Gefahrenfilter / فلاتر المخاطر" in text
    assert "Voice announcement / Sprachansage / إعلان صوتي" in text
