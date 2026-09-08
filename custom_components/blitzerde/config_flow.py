"""Config and options flows for Blitzer.de."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_CONDITION,
    CONF_COUNT,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_TYPE,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import selector
from homeassistant.util import slugify

from .api import APIConnectionError, BlitzerdeAPI
from .const import (
    CONF_OPTIONAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_ONLY_CONFIRMED,
    DEFAULT_SELECTOR,
    DEFAULT_SENSOR_COUNT,
    DEFAULT_TYPES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SENSOR_COUNT,
    MAX_UPDATE_INTERVAL_MINUTES,
    TYPE_FIXED,
    TYPE_MOBILE,
    TYPE_TRAILER,
)


class BlitzerdeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blitzer.de."""

    VERSION = 6

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
        """Handle initial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized = _normalize_input(user_input)
            validation_error = _validate_local_input(
                normalized
            )
            if validation_error:
                errors["base"] = validation_error
            else:
                try:
                    await _async_test_connection(
                        self.hass, normalized
                    )
                except APIConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(
                        slugify(normalized[CONF_NAME])
                    )
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=(
                            f"Blitzer.de "
                            f"{normalized[CONF_NAME]}"
                        ),
                        data=normalized,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return BlitzerdeOptionsFlow()


class BlitzerdeOptionsFlow(config_entries.OptionsFlow):
    """Handle runtime options without mutating initial config data."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ):
        """Manage Blitzer.de options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized = _normalize_input(
                user_input,
                name=str(
                    self.config_entry.data.get(
                        CONF_NAME,
                        self.config_entry.title,
                    )
                ),
            )
            validation_error = _validate_local_input(
                normalized
            )
            if validation_error:
                errors["base"] = validation_error
            else:
                try:
                    await _async_test_connection(
                        self.hass, normalized
                    )
                except APIConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    options = {
                        CONF_LOCATION: normalized[
                            CONF_LOCATION
                        ],
                        CONF_TYPE: normalized[CONF_TYPE],
                        CONF_COUNT: normalized[CONF_COUNT],
                        CONF_SELECTOR: normalized[
                            CONF_SELECTOR
                        ],
                        CONF_CONDITION: normalized[
                            CONF_CONDITION
                        ],
                        CONF_UPDATE_INTERVAL: normalized[
                            CONF_UPDATE_INTERVAL
                        ],
                    }
                    return self.async_create_entry(
                        title="", data=options
                    )

        current = {
            **dict(self.config_entry.data),
            **dict(self.config_entry.options),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(
                current, include_name=False
            ),
            errors=errors,
        )


def _build_schema(
    values: dict[str, Any] | None,
    *,
    include_name: bool = True,
) -> vol.Schema:
    """Build the shared config/options form schema."""
    values = values or {}
    types = values.get(CONF_TYPE, DEFAULT_TYPES)
    optional = values.get(CONF_OPTIONAL, {})

    default_count = values.get(
        CONF_COUNT,
        optional.get(
            CONF_COUNT, DEFAULT_SENSOR_COUNT
        ),
    )
    default_selector = values.get(
        CONF_SELECTOR,
        optional.get(
            CONF_SELECTOR, DEFAULT_SELECTOR
        ),
    )
    default_condition = values.get(
        CONF_CONDITION,
        optional.get(
            CONF_CONDITION,
            DEFAULT_ONLY_CONFIRMED,
        ),
    )
    default_update_interval = values.get(
        CONF_UPDATE_INTERVAL,
        optional.get(
            CONF_UPDATE_INTERVAL,
            DEFAULT_UPDATE_INTERVAL_MINUTES,
        ),
    )

    schema: dict[Any, Any] = {}
    if include_name:
        schema[
            vol.Required(
                CONF_NAME,
                default=values.get(CONF_NAME, "Home"),
            )
        ] = str

    location_key = (
        vol.Required(
            CONF_LOCATION,
            default=values[CONF_LOCATION],
        )
        if CONF_LOCATION in values
        and values[CONF_LOCATION] is not None
        else vol.Required(CONF_LOCATION)
    )
    schema[location_key] = selector(
        {"location": {"radius": True}}
    )
    schema[vol.Required(CONF_TYPE)] = section(
        vol.Schema(
            {
                vol.Required(
                    "mobile",
                    default=types.get("mobile", True),
                ): bool,
                vol.Required(
                    "trailer",
                    default=types.get("trailer", True),
                ): bool,
                vol.Required(
                    "fixed",
                    default=types.get("fixed", False),
                ): bool,
            }
        ),
        {"collapsed": False},
    )
    schema[vol.Required(CONF_OPTIONAL)] = section(
        vol.Schema(
            {
                vol.Required(
                    CONF_COUNT,
                    default=default_count,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=1,
                        max=MAX_SENSOR_COUNT,
                    ),
                ),
                vol.Required(
                    CONF_SELECTOR,
                    default=default_selector,
                ): str,
                vol.Required(
                    CONF_CONDITION,
                    default=default_condition,
                ): bool,
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=default_update_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=0,
                        max=MAX_UPDATE_INTERVAL_MINUTES,
                    ),
                ),
            }
        ),
        {"collapsed": True},
    )
    return vol.Schema(schema)


def _normalize_input(
    user_input: dict[str, Any],
    *,
    name: str | None = None,
) -> dict[str, Any]:
    """Flatten optional UI data into config-entry friendly values."""
    optional = user_input.get(CONF_OPTIONAL, {})
    return {
        CONF_NAME: (
            name
            if name is not None
            else str(
                user_input.get(CONF_NAME, "Home")
            )
        ),
        CONF_LOCATION: user_input.get(CONF_LOCATION),
        CONF_TYPE: dict(
            user_input.get(
                CONF_TYPE, DEFAULT_TYPES
            )
        ),
        CONF_COUNT: int(
            optional.get(
                CONF_COUNT,
                user_input.get(
                    CONF_COUNT,
                    DEFAULT_SENSOR_COUNT,
                ),
            )
        ),
        CONF_SELECTOR: str(
            optional.get(
                CONF_SELECTOR,
                user_input.get(
                    CONF_SELECTOR,
                    DEFAULT_SELECTOR,
                ),
            )
        ),
        CONF_CONDITION: bool(
            optional.get(
                CONF_CONDITION,
                user_input.get(
                    CONF_CONDITION,
                    DEFAULT_ONLY_CONFIRMED,
                ),
            )
        ),
        CONF_UPDATE_INTERVAL: int(
            optional.get(
                CONF_UPDATE_INTERVAL,
                user_input.get(
                    CONF_UPDATE_INTERVAL,
                    DEFAULT_UPDATE_INTERVAL_MINUTES,
                ),
            )
        ),
    }


def _validate_local_input(
    data: dict[str, Any],
) -> str | None:
    """Validate non-network input and return a translation key."""
    location = data.get(CONF_LOCATION)
    if not str(data.get(CONF_NAME, "")).strip():
        return "invalid_name"
    if not isinstance(location, dict):
        return "location_missing"
    if not {
        "latitude",
        "longitude",
        "radius",
    }.issubset(location):
        return "location_missing"
    if not any(data[CONF_TYPE].values()):
        return "no_types_selected"
    try:
        re.compile(data[CONF_SELECTOR])
    except re.error:
        return "invalid_regex"
    return None


def _enabled_types(
    data: dict[str, Any],
) -> list[int | str]:
    """Convert UI type toggles to upstream type IDs."""
    result: list[int | str] = []
    types = data[CONF_TYPE]
    if types.get("mobile"):
        result.extend(TYPE_MOBILE)
    if types.get("trailer"):
        result.extend(TYPE_TRAILER)
    if types.get("fixed"):
        result.extend(TYPE_FIXED)
    return result


async def _async_test_connection(
    hass, data: dict[str, Any]
) -> None:
    """Ensure the endpoint works before accepting a configuration."""
    api = BlitzerdeAPI(hass)
    location = data[CONF_LOCATION]
    await api.async_test_connection(
        latitude=float(location["latitude"]),
        longitude=float(location["longitude"]),
        radius=float(location["radius"]),
        types=_enabled_types(data),
    )
