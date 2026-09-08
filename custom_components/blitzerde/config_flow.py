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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import selector
from homeassistant.util import slugify

from .api import APIConnectionError, BlitzerdeAPI
from .const import (
    CONF_BLACKLIST,
    CONF_CORRIDOR_WIDTH,
    CONF_NEW_MINUTES,
    CONF_OPTIONAL,
    CONF_SEARCH_MODE,
    CONF_UPDATE_INTERVAL,
    CONF_WAYPOINTS,
    DEFAULT_BLACKLIST,
    DEFAULT_CORRIDOR_WIDTH_METERS,
    DEFAULT_NEW_MINUTES,
    DEFAULT_ONLY_CONFIRMED,
    DEFAULT_SELECTOR,
    DEFAULT_SENSOR_COUNT,
    DEFAULT_TYPES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_CORRIDOR_WIDTH_METERS,
    MAX_NEW_MINUTES,
    MAX_ROUTE_QUERY_POINTS,
    MAX_SENSOR_COUNT,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_CORRIDOR_WIDTH_METERS,
    SEARCH_MODE_AREA,
    SEARCH_MODE_ROUTE,
    TYPE_FIXED,
    TYPE_MOBILE,
    TYPE_TRAILER,
)
from .route import route_query_count

_ADD_ANOTHER = "add_another"


class BlitzerdeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Blitzer.de."""

    VERSION = 8

    def __init__(self) -> None:
        """Initialize the multi-step flow."""
        self._name = ""
        self._waypoints: list[dict[str, float]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
        """Choose a name and search mode."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = str(user_input.get(CONF_NAME, "")).strip()
            if not name:
                errors["base"] = "invalid_name"
            else:
                await self.async_set_unique_id(slugify(name))
                self._abort_if_unique_id_configured()
                if any(
                    slugify(
                        str(entry.data.get(CONF_NAME, ""))
                    )
                    == slugify(name)
                    for entry in self._async_current_entries()
                ):
                    return self.async_abort(
                        reason="already_configured"
                    )

                self._name = name
                if (
                    user_input[CONF_SEARCH_MODE]
                    == SEARCH_MODE_ROUTE
                ):
                    self._waypoints = []
                    return await self.async_step_waypoint()
                return await self.async_step_area()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(
                        CONF_SEARCH_MODE,
                        default=SEARCH_MODE_AREA,
                    ): selector(
                        {
                            "select": {
                                "options": [
                                    SEARCH_MODE_AREA,
                                    SEARCH_MODE_ROUTE,
                                ],
                                "translation_key": "search_mode",
                                "mode": "list",
                            }
                        }
                    ),
                }
            ),
            errors=errors,
            last_step=False,
        )

    async def async_step_area(
        self, user_input: dict[str, Any] | None = None
    ):
        """Configure a circular area search."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_common(
                user_input, name=self._name
            )
            data[CONF_SEARCH_MODE] = SEARCH_MODE_AREA
            data[CONF_LOCATION] = user_input.get(
                CONF_LOCATION
            )

            validation_error = _validate_area(data)
            if validation_error:
                errors["base"] = validation_error
            else:
                try:
                    await _async_test_area_connection(
                        self.hass, data
                    )
                except APIConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=f"Blitzer.de {self._name}",
                        data=data,
                    )

        return self.async_show_form(
            step_id="area",
            data_schema=_area_schema(
                {
                    CONF_LOCATION: {
                        "latitude": self.hass.config.latitude,
                        "longitude": self.hass.config.longitude,
                        "radius": 1500,
                    }
                }
            ),
            errors=errors,
            last_step=True,
        )

    async def async_step_waypoint(
        self, user_input: dict[str, Any] | None = None
    ):
        """Collect route waypoints one map screen at a time."""
        errors: dict[str, str] = {}

        if user_input is not None:
            location = user_input.get(CONF_LOCATION)
            if not isinstance(location, dict):
                errors["base"] = "location_missing"
            else:
                self._waypoints.append(
                    {
                        "latitude": float(
                            location["latitude"]
                        ),
                        "longitude": float(
                            location["longitude"]
                        ),
                    }
                )
                if not user_input[_ADD_ANOTHER]:
                    if len(self._waypoints) < 2:
                        errors["base"] = (
                            "route_needs_two_waypoints"
                        )
                    else:
                        return (
                            await self.async_step_route_options()
                        )

        default_location = (
            self._waypoints[-1]
            if self._waypoints
            else {
                "latitude": self.hass.config.latitude,
                "longitude": self.hass.config.longitude,
            }
        )
        return self.async_show_form(
            step_id="waypoint",
            data_schema=_waypoint_schema(
                default_location
            ),
            errors=errors,
            description_placeholders={
                "count": str(len(self._waypoints) + 1)
            },
            last_step=False,
        )

    async def async_step_route_options(
        self, user_input: dict[str, Any] | None = None
    ):
        """Configure route corridor and report filters."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_common(
                user_input, name=self._name
            )
            data.update(
                {
                    CONF_SEARCH_MODE: SEARCH_MODE_ROUTE,
                    CONF_WAYPOINTS: list(self._waypoints),
                    CONF_CORRIDOR_WIDTH: int(
                        user_input[CONF_CORRIDOR_WIDTH]
                    ),
                }
            )

            validation_error = _validate_route(data)
            if validation_error:
                errors["base"] = validation_error
            else:
                try:
                    await _async_test_route_connection(
                        self.hass, data
                    )
                except APIConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=f"Blitzer.de {self._name}",
                        data=data,
                    )

        return self.async_show_form(
            step_id="route_options",
            data_schema=_route_schema({}),
            errors=errors,
            last_step=True,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return BlitzerdeOptionsFlow()


class BlitzerdeOptionsFlow(config_entries.OptionsFlow):
    """Handle runtime options for area and route entries."""

    def __init__(self) -> None:
        """Initialize options state."""
        self._waypoints: list[dict[str, float]] = []

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ):
        """Route entries get a menu; area entries open directly."""
        if (
            self.config_entry.data.get(
                CONF_SEARCH_MODE, SEARCH_MODE_AREA
            )
            == SEARCH_MODE_ROUTE
        ):
            return self.async_show_menu(
                step_id="init",
                menu_options=[
                    "route_settings",
                    "edit_waypoints",
                ],
            )
        return await self.async_step_area(user_input)

    async def async_step_area(
        self, user_input: dict[str, Any] | None = None
    ):
        """Edit an area entry."""
        errors: dict[str, str] = {}
        current = _current_values(self.config_entry)

        if user_input is not None:
            data = _normalize_common(
                user_input,
                name=str(
                    self.config_entry.data.get(
                        CONF_NAME,
                        self.config_entry.title,
                    )
                ),
            )
            data[CONF_SEARCH_MODE] = SEARCH_MODE_AREA
            data[CONF_LOCATION] = user_input.get(
                CONF_LOCATION
            )

            validation_error = _validate_area(data)
            if validation_error:
                errors["base"] = validation_error
            else:
                try:
                    await _async_test_area_connection(
                        self.hass, data
                    )
                except APIConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title="",
                        data=_runtime_options(data),
                    )

        return self.async_show_form(
            step_id="area",
            data_schema=_area_schema(current),
            errors=errors,
        )

    async def async_step_route_settings(
        self, user_input: dict[str, Any] | None = None
    ):
        """Edit corridor width and filters without redrawing the route."""
        errors: dict[str, str] = {}
        current = _current_values(self.config_entry)
        waypoints = (
            self._waypoints
            or list(current.get(CONF_WAYPOINTS, []))
        )

        if user_input is not None:
            data = _normalize_common(
                user_input,
                name=str(
                    self.config_entry.data.get(
                        CONF_NAME,
                        self.config_entry.title,
                    )
                ),
            )
            data.update(
                {
                    CONF_SEARCH_MODE: SEARCH_MODE_ROUTE,
                    CONF_WAYPOINTS: waypoints,
                    CONF_CORRIDOR_WIDTH: int(
                        user_input[CONF_CORRIDOR_WIDTH]
                    ),
                }
            )

            validation_error = _validate_route(data)
            if validation_error:
                errors["base"] = validation_error
            else:
                try:
                    await _async_test_route_connection(
                        self.hass, data
                    )
                except APIConnectionError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title="",
                        data=_runtime_options(data),
                    )

        route_defaults = dict(current)
        route_defaults[CONF_WAYPOINTS] = waypoints
        return self.async_show_form(
            step_id="route_settings",
            data_schema=_route_schema(route_defaults),
            errors=errors,
        )

    async def async_step_edit_waypoints(
        self, user_input: dict[str, Any] | None = None
    ):
        """Start a clean waypoint redraw for an existing route."""
        self._waypoints = []
        return await self.async_step_route_waypoint()

    async def async_step_route_waypoint(
        self, user_input: dict[str, Any] | None = None
    ):
        """Collect replacement route waypoints."""
        errors: dict[str, str] = {}

        if user_input is not None:
            location = user_input.get(CONF_LOCATION)
            if not isinstance(location, dict):
                errors["base"] = "location_missing"
            else:
                self._waypoints.append(
                    {
                        "latitude": float(
                            location["latitude"]
                        ),
                        "longitude": float(
                            location["longitude"]
                        ),
                    }
                )
                if not user_input[_ADD_ANOTHER]:
                    if len(self._waypoints) < 2:
                        errors["base"] = (
                            "route_needs_two_waypoints"
                        )
                    else:
                        return (
                            await self.async_step_route_settings()
                        )

        existing = _current_values(
            self.config_entry
        ).get(CONF_WAYPOINTS, [])
        default_location = (
            self._waypoints[-1]
            if self._waypoints
            else (
                existing[0]
                if existing
                else {
                    "latitude": self.hass.config.latitude,
                    "longitude": self.hass.config.longitude,
                }
            )
        )

        return self.async_show_form(
            step_id="route_waypoint",
            data_schema=_waypoint_schema(
                default_location
            ),
            errors=errors,
            description_placeholders={
                "count": str(len(self._waypoints) + 1)
            },
        )


def _common_schema(values: dict[str, Any]) -> dict[Any, Any]:
    """Return shared camera type and advanced option fields."""
    types = values.get(CONF_TYPE, DEFAULT_TYPES)

    return {
        vol.Required(CONF_TYPE): section(
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
        ),
        vol.Required(CONF_OPTIONAL): section(
            vol.Schema(
                {
                    vol.Required(
                        CONF_COUNT,
                        default=values.get(
                            CONF_COUNT,
                            DEFAULT_SENSOR_COUNT,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=1,
                            max=MAX_SENSOR_COUNT,
                        ),
                    ),
                    vol.Required(
                        CONF_SELECTOR,
                        default=values.get(
                            CONF_SELECTOR,
                            DEFAULT_SELECTOR,
                        ),
                    ): str,
                    vol.Required(
                        CONF_CONDITION,
                        default=values.get(
                            CONF_CONDITION,
                            DEFAULT_ONLY_CONFIRMED,
                        ),
                    ): bool,
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=values.get(
                            CONF_UPDATE_INTERVAL,
                            DEFAULT_UPDATE_INTERVAL_MINUTES,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=0,
                            max=MAX_UPDATE_INTERVAL_MINUTES,
                        ),
                    ),
                    vol.Required(
                        CONF_NEW_MINUTES,
                        default=values.get(
                            CONF_NEW_MINUTES,
                            DEFAULT_NEW_MINUTES,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=0,
                            max=MAX_NEW_MINUTES,
                        ),
                    ),
                    vol.Required(
                        CONF_BLACKLIST,
                        default=values.get(
                            CONF_BLACKLIST,
                            DEFAULT_BLACKLIST,
                        ),
                    ): str,
                }
            ),
            {"collapsed": True},
        ),
    }


def _area_schema(values: dict[str, Any]) -> vol.Schema:
    """Build a radius search form."""
    location = values.get(CONF_LOCATION)
    if not isinstance(location, dict):
        location = {
            "latitude": 51.0504,
            "longitude": 13.7373,
            "radius": 1500,
        }

    return vol.Schema(
        {
            vol.Required(
                CONF_LOCATION, default=location
            ): selector({"location": {"radius": True}}),
            **_common_schema(values),
        }
    )


def _route_schema(values: dict[str, Any]) -> vol.Schema:
    """Build corridor/filter settings for a route."""
    return vol.Schema(
        {
            vol.Required(
                CONF_CORRIDOR_WIDTH,
                default=values.get(
                    CONF_CORRIDOR_WIDTH,
                    DEFAULT_CORRIDOR_WIDTH_METERS,
                ),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(
                    min=MIN_CORRIDOR_WIDTH_METERS,
                    max=MAX_CORRIDOR_WIDTH_METERS,
                ),
            ),
            **_common_schema(values),
        }
    )


def _waypoint_schema(
    default_location: dict[str, float],
) -> vol.Schema:
    """Build one waypoint screen."""
    return vol.Schema(
        {
            vol.Required(
                CONF_LOCATION,
                default=default_location,
            ): selector({"location": {}}),
            vol.Required(
                _ADD_ANOTHER, default=True
            ): bool,
        }
    )


def _normalize_common(
    user_input: dict[str, Any],
    *,
    name: str,
) -> dict[str, Any]:
    """Flatten common sections into config-entry friendly data."""
    optional = user_input.get(CONF_OPTIONAL, {})
    return {
        CONF_NAME: name,
        CONF_TYPE: dict(
            user_input.get(
                CONF_TYPE, DEFAULT_TYPES
            )
        ),
        CONF_COUNT: int(
            optional.get(
                CONF_COUNT, DEFAULT_SENSOR_COUNT
            )
        ),
        CONF_SELECTOR: str(
            optional.get(
                CONF_SELECTOR, DEFAULT_SELECTOR
            )
        ),
        CONF_CONDITION: bool(
            optional.get(
                CONF_CONDITION,
                DEFAULT_ONLY_CONFIRMED,
            )
        ),
        CONF_UPDATE_INTERVAL: int(
            optional.get(
                CONF_UPDATE_INTERVAL,
                DEFAULT_UPDATE_INTERVAL_MINUTES,
            )
        ),
        CONF_NEW_MINUTES: int(
            optional.get(
                CONF_NEW_MINUTES,
                DEFAULT_NEW_MINUTES,
            )
        ),
        CONF_BLACKLIST: str(
            optional.get(
                CONF_BLACKLIST,
                DEFAULT_BLACKLIST,
            )
        ).strip(),
    }


def _current_values(entry: ConfigEntry) -> dict[str, Any]:
    """Merge initial data and current options."""
    return {
        **dict(entry.data),
        **dict(entry.options),
    }


def _runtime_options(data: dict[str, Any]) -> dict[str, Any]:
    """Keep mutable runtime values out of immutable identity fields."""
    keys = {
        CONF_LOCATION,
        CONF_WAYPOINTS,
        CONF_CORRIDOR_WIDTH,
        CONF_TYPE,
        CONF_COUNT,
        CONF_SELECTOR,
        CONF_CONDITION,
        CONF_UPDATE_INTERVAL,
        CONF_NEW_MINUTES,
        CONF_BLACKLIST,
    }
    return {
        key: value
        for key, value in data.items()
        if key in keys
    }


def _validate_common(
    data: dict[str, Any],
) -> str | None:
    """Validate types and city filter."""
    if not any(data[CONF_TYPE].values()):
        return "no_types_selected"
    try:
        re.compile(data[CONF_SELECTOR])
    except re.error:
        return "invalid_regex"
    return None


def _validate_area(
    data: dict[str, Any],
) -> str | None:
    """Validate a radius search."""
    if error := _validate_common(data):
        return error

    location = data.get(CONF_LOCATION)
    if not isinstance(location, dict):
        return "location_missing"
    if not {
        "latitude",
        "longitude",
        "radius",
    }.issubset(location):
        return "location_missing"
    return None


def _validate_route(
    data: dict[str, Any],
) -> str | None:
    """Validate a route without issuing API requests."""
    if error := _validate_common(data):
        return error

    waypoints = data.get(CONF_WAYPOINTS)
    if not isinstance(waypoints, list) or len(waypoints) < 2:
        return "route_needs_two_waypoints"

    count = route_query_count(
        waypoints,
        float(data[CONF_CORRIDOR_WIDTH]),
    )
    if count > MAX_ROUTE_QUERY_POINTS:
        return "route_too_large"
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


async def _async_test_area_connection(
    hass: Any, data: dict[str, Any]
) -> None:
    """Ensure the endpoint works for an area config."""
    api = BlitzerdeAPI(async_get_clientsession(hass))
    location = data[CONF_LOCATION]
    await api.async_test_connection(
        latitude=float(location["latitude"]),
        longitude=float(location["longitude"]),
        radius=float(location["radius"]),
        types=_enabled_types(data),
    )


async def _async_test_route_connection(
    hass: Any, data: dict[str, Any]
) -> None:
    """Ensure the endpoint works using the first route waypoint."""
    api = BlitzerdeAPI(async_get_clientsession(hass))
    first = data[CONF_WAYPOINTS][0]
    await api.async_test_connection(
        latitude=float(first["latitude"]),
        longitude=float(first["longitude"]),
        radius=float(data[CONF_CORRIDOR_WIDTH]),
        types=_enabled_types(data),
    )
