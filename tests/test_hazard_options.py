"""Tests for traffic-hazard config/options helpers."""

from custom_components.blitzerde.const import (
    CONF_HAZARD_BLACKLIST,
    CONF_HAZARD_COUNT,
    CONF_HAZARD_NEW_MINUTES,
    CONF_HAZARD_SELECTOR,
    CONF_HAZARD_UPDATE_INTERVAL,
    CONF_HAZARDS,
    HAZARD_DEFAULTS,
)
from custom_components.blitzerde.hazard_options import (
    enabled_hazard_kinds,
    hazard_schema,
    normalize_hazard_options,
    validate_hazard_options,
)


def test_hazard_schema_is_opt_in_by_default() -> None:
    """The UI must preserve zero-background-work defaults."""
    schema = hazard_schema({})

    assert schema
    normalized = normalize_hazard_options({})
    assert normalized[CONF_HAZARDS] == HAZARD_DEFAULTS
    assert normalized[CONF_HAZARD_UPDATE_INTERVAL] == 0


def test_normalize_hazard_options_flattens_sections() -> None:
    """Nested UI sections become stable config-entry options."""
    result = normalize_hazard_options(
        {
            CONF_HAZARDS: {
                "accident": True,
                "closure": True,
                "future_unknown_kind": True,
            },
            "hazard_optional": {
                CONF_HAZARD_COUNT: "12",
                CONF_HAZARD_SELECTOR: "Dresden|Meißen",
                CONF_HAZARD_UPDATE_INTERVAL: "5",
                CONF_HAZARD_NEW_MINUTES: "30",
                CONF_HAZARD_BLACKLIST: " 123,456 ",
            },
        }
    )

    assert result[CONF_HAZARDS]["accident"] is True
    assert result[CONF_HAZARDS]["closure"] is True
    assert "future_unknown_kind" not in result[CONF_HAZARDS]
    assert result[CONF_HAZARD_COUNT] == 12
    assert result[CONF_HAZARD_SELECTOR] == "Dresden|Meißen"
    assert result[CONF_HAZARD_UPDATE_INTERVAL] == 5
    assert result[CONF_HAZARD_NEW_MINUTES] == 30
    assert result[CONF_HAZARD_BLACKLIST] == "123,456"


def test_validate_hazard_options_rejects_invalid_regex() -> None:
    """Hazard city filtering gets its own validation error."""
    assert (
        validate_hazard_options({CONF_HAZARD_SELECTOR: "["})
        == "invalid_hazard_regex"
    )
    assert validate_hazard_options({CONF_HAZARD_SELECTOR: ".*"}) is None


def test_enabled_hazard_kinds_follow_taxonomy_order() -> None:
    """Enabled kinds stay deterministic for API queries and diagnostics."""
    configured = {key: False for key in HAZARD_DEFAULTS}
    configured["accident"] = True
    configured["closure"] = True

    assert enabled_hazard_kinds({CONF_HAZARDS: configured}) == (
        "accident",
        "closure",
    )


def test_hazard_blacklist_field_is_optional_for_empty_default() -> None:
    """An empty hazard blacklist must not block the Home Assistant form."""
    import voluptuous as vol

    schema = hazard_schema({})
    optional_section = next(
        value
        for marker, value in schema.items()
        if getattr(marker, "schema", None) == "hazard_optional"
    )
    nested_schema = getattr(optional_section, "schema", optional_section)
    if hasattr(nested_schema, "schema"):
        nested_schema = nested_schema.schema
    blacklist_marker = next(
        marker
        for marker in nested_schema
        if getattr(marker, "schema", None) == CONF_HAZARD_BLACKLIST
    )

    assert isinstance(blacklist_marker, vol.Optional)
