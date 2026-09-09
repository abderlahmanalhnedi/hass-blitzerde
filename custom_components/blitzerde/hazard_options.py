"""Reusable schema and normalization helpers for traffic-hazard options."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant.data_entry_flow import section

from .const import (
    CONF_HAZARD_BLACKLIST,
    CONF_HAZARD_COUNT,
    CONF_HAZARD_NEW_MINUTES,
    CONF_HAZARD_SELECTOR,
    CONF_HAZARD_UPDATE_INTERVAL,
    CONF_HAZARDS,
    DEFAULT_BLACKLIST,
    DEFAULT_HAZARD_COUNT,
    DEFAULT_NEW_MINUTES,
    DEFAULT_SELECTOR,
    HAZARD_DEFAULTS,
    MAX_NEW_MINUTES,
    MAX_SENSOR_COUNT,
    MAX_UPDATE_INTERVAL_MINUTES,
)


def hazard_schema(values: dict[str, Any]) -> dict[Any, Any]:
    """Return a collapsible hazard configuration section for config flows."""
    hazards = values.get(CONF_HAZARDS, HAZARD_DEFAULTS)
    if not isinstance(hazards, dict):
        hazards = HAZARD_DEFAULTS

    return {
        vol.Required(CONF_HAZARDS): section(
            vol.Schema(
                {
                    vol.Required(
                        key,
                        default=bool(hazards.get(key, default)),
                    ): bool
                    for key, default in HAZARD_DEFAULTS.items()
                }
            ),
            {"collapsed": True},
        ),
        vol.Required("hazard_optional"): section(
            vol.Schema(
                {
                    vol.Required(
                        CONF_HAZARD_COUNT,
                        default=values.get(
                            CONF_HAZARD_COUNT,
                            DEFAULT_HAZARD_COUNT,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=MAX_SENSOR_COUNT),
                    ),
                    vol.Required(
                        CONF_HAZARD_SELECTOR,
                        default=values.get(
                            CONF_HAZARD_SELECTOR,
                            DEFAULT_SELECTOR,
                        ),
                    ): str,
                    vol.Required(
                        CONF_HAZARD_UPDATE_INTERVAL,
                        default=values.get(CONF_HAZARD_UPDATE_INTERVAL, 0),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=0, max=MAX_UPDATE_INTERVAL_MINUTES),
                    ),
                    vol.Required(
                        CONF_HAZARD_NEW_MINUTES,
                        default=values.get(
                            CONF_HAZARD_NEW_MINUTES,
                            DEFAULT_NEW_MINUTES,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=0, max=MAX_NEW_MINUTES),
                    ),
                    vol.Optional(
                        CONF_HAZARD_BLACKLIST,
                        default=values.get(
                            CONF_HAZARD_BLACKLIST,
                            DEFAULT_BLACKLIST,
                        ),
                    ): str,
                }
            ),
            {"collapsed": True},
        ),
    }


def normalize_hazard_options(user_input: dict[str, Any]) -> dict[str, Any]:
    """Flatten hazard sections into config-entry friendly runtime options."""
    raw_hazards = user_input.get(CONF_HAZARDS, HAZARD_DEFAULTS)
    hazards = {
        key: bool(raw_hazards.get(key, default))
        for key, default in HAZARD_DEFAULTS.items()
    }
    optional = user_input.get("hazard_optional", {})

    return {
        CONF_HAZARDS: hazards,
        CONF_HAZARD_COUNT: int(
            optional.get(CONF_HAZARD_COUNT, DEFAULT_HAZARD_COUNT)
        ),
        CONF_HAZARD_SELECTOR: str(
            optional.get(CONF_HAZARD_SELECTOR, DEFAULT_SELECTOR)
        ),
        CONF_HAZARD_UPDATE_INTERVAL: int(
            optional.get(CONF_HAZARD_UPDATE_INTERVAL, 0)
        ),
        CONF_HAZARD_NEW_MINUTES: int(
            optional.get(CONF_HAZARD_NEW_MINUTES, DEFAULT_NEW_MINUTES)
        ),
        CONF_HAZARD_BLACKLIST: str(
            optional.get(CONF_HAZARD_BLACKLIST, DEFAULT_BLACKLIST)
        ).strip(),
    }


def validate_hazard_options(data: dict[str, Any]) -> str | None:
    """Validate hazard filters without requiring hazards to be enabled."""
    try:
        re.compile(str(data.get(CONF_HAZARD_SELECTOR, DEFAULT_SELECTOR)))
    except re.error:
        return "invalid_hazard_regex"
    return None


def enabled_hazard_kinds(data: dict[str, Any]) -> tuple[str, ...]:
    """Return enabled semantic hazard kinds in stable taxonomy order."""
    configured = data.get(CONF_HAZARDS, HAZARD_DEFAULTS)
    if not isinstance(configured, dict):
        return ()
    return tuple(
        key
        for key in HAZARD_DEFAULTS
        if bool(configured.get(key, False))
    )
