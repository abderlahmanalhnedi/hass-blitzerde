"""Translation contract tests for config-flow abort reasons."""

from __future__ import annotations

import json
from pathlib import Path

INTEGRATION_DIR = Path("custom_components/blitzerde")
TRANSLATION_FILES = (
    INTEGRATION_DIR / "strings.json",
    INTEGRATION_DIR / "translations/en.json",
    INTEGRATION_DIR / "translations/de.json",
    INTEGRATION_DIR / "translations/ar.json",
)


def test_already_in_progress_abort_reason_is_translated() -> None:
    """Keep Home Assistant from exposing the raw abort key to users."""
    for path in TRANSLATION_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        message = data["config"]["abort"]["already_in_progress"]

        assert isinstance(message, str)
        assert message.strip()
        assert message != "already_in_progress"
