"""Home Assistant config-flow tests for Blitzer.de."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_CONDITION,
    CONF_COUNT,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_TYPE,
)
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.blitzerde.api import APIConnectionError
from custom_components.blitzerde.const import (
    CONF_BLACKLIST,
    CONF_CORRIDOR_WIDTH,
    CONF_NEW_MINUTES,
    CONF_OPTIONAL,
    CONF_SEARCH_MODE,
    CONF_UPDATE_INTERVAL,
    CONF_WAYPOINTS,
    DOMAIN,
    SEARCH_MODE_AREA,
    SEARCH_MODE_ROUTE,
)

AREA_LOCATION = {
    "latitude": 51.0504,
    "longitude": 13.7373,
    "radius": 2000,
}
ROUTE_START = {
    "latitude": 51.0504,
    "longitude": 13.7373,
}
ROUTE_END = {
    "latitude": 51.0604,
    "longitude": 13.7573,
}
TYPE_INPUT = {
    "mobile": True,
    "trailer": True,
    "fixed": False,
}
OPTIONAL_INPUT = {
    CONF_COUNT: 9,
    CONF_SELECTOR: ".*",
    CONF_CONDITION: True,
    CONF_UPDATE_INTERVAL: 1,
    CONF_NEW_MINUTES: 60,
    CONF_BLACKLIST: "",
}
AREA_INPUT = {
    CONF_LOCATION: AREA_LOCATION,
    CONF_TYPE: TYPE_INPUT,
    CONF_OPTIONAL: OPTIONAL_INPUT,
}
ROUTE_OPTIONS_INPUT = {
    CONF_CORRIDOR_WIDTH: 500,
    CONF_TYPE: TYPE_INPUT,
    CONF_OPTIONAL: OPTIONAL_INPUT,
}


async def _start_flow(hass, *, name: str, mode: str):
    """Start a user flow and select its search mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: name,
            CONF_SEARCH_MODE: mode,
        },
    )


async def test_area_happy_path(hass) -> None:
    """An area can be configured fully from the UI."""
    result = await _start_flow(
        hass, name="Dresden", mode=SEARCH_MODE_AREA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "area"

    with patch(
        "custom_components.blitzerde.config_flow.BlitzerdeAPI.async_test_connection",
        new_callable=AsyncMock,
    ) as test_connection:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], AREA_INPUT
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Blitzer.de Dresden"
    assert result["data"][CONF_SEARCH_MODE] == SEARCH_MODE_AREA
    assert result["data"][CONF_LOCATION] == AREA_LOCATION
    test_connection.assert_awaited_once()


async def test_area_recovers_after_connection_error(hass) -> None:
    """A temporary upstream failure does not trap the config flow."""
    result = await _start_flow(
        hass, name="Recovery", mode=SEARCH_MODE_AREA
    )

    with patch(
        "custom_components.blitzerde.config_flow.BlitzerdeAPI.async_test_connection",
        new=AsyncMock(
            side_effect=[
                APIConnectionError("temporary failure"),
                None,
            ]
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], AREA_INPUT
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "area"
        assert result["errors"] == {"base": "cannot_connect"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], AREA_INPUT
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_rejects_empty_name(hass) -> None:
    """The first step rejects an empty display name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "   ",
            CONF_SEARCH_MODE: SEARCH_MODE_AREA,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_name"}


async def test_duplicate_name_is_rejected(hass) -> None:
    """A configured area cannot be added again under the same identity."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        unique_id="dresden",
        data={
            CONF_NAME: "Dresden",
            CONF_SEARCH_MODE: SEARCH_MODE_AREA,
            CONF_LOCATION: AREA_LOCATION,
            CONF_TYPE: TYPE_INPUT,
            **OPTIONAL_INPUT,
        },
    )
    entry.add_to_hass(hass)

    result = await _start_flow(
        hass, name="Dresden", mode=SEARCH_MODE_AREA
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_area_validation_errors(hass) -> None:
    """Local validation rejects bad report types and city regex."""
    result = await _start_flow(
        hass, name="Validation", mode=SEARCH_MODE_AREA
    )

    no_types = {
        **AREA_INPUT,
        CONF_TYPE: {
            "mobile": False,
            "trailer": False,
            "fixed": False,
        },
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], no_types
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_types_selected"}

    invalid_regex = {
        **AREA_INPUT,
        CONF_OPTIONAL: {
            **OPTIONAL_INPUT,
            CONF_SELECTOR: "[",
        },
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], invalid_regex
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_regex"}


async def test_route_happy_path(hass) -> None:
    """A waypoint route can be created through the multi-step flow."""
    result = await _start_flow(
        hass, name="Commute", mode=SEARCH_MODE_ROUTE
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "waypoint"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: ROUTE_START,
            "add_another": True,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "waypoint"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: ROUTE_END,
            "add_another": False,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "route_options"

    with patch(
        "custom_components.blitzerde.config_flow.BlitzerdeAPI.async_test_connection",
        new_callable=AsyncMock,
    ) as test_connection:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], ROUTE_OPTIONS_INPUT
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SEARCH_MODE] == SEARCH_MODE_ROUTE
    assert result["data"][CONF_WAYPOINTS] == [
        ROUTE_START,
        ROUTE_END,
    ]
    assert result["data"][CONF_CORRIDOR_WIDTH] == 500
    test_connection.assert_awaited_once()


async def test_route_requires_two_waypoints_and_recovers(hass) -> None:
    """The route wizard explains and recovers from a one-point route."""
    result = await _start_flow(
        hass, name="Short route", mode=SEARCH_MODE_ROUTE
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: ROUTE_START,
            "add_another": False,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "waypoint"
    assert result["errors"] == {
        "base": "route_needs_two_waypoints"
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: ROUTE_END,
            "add_another": False,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "route_options"


async def test_area_options_flow(hass) -> None:
    """Mutable area settings are stored in ConfigEntry.options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        unique_id="dresden",
        data={
            CONF_NAME: "Dresden",
            CONF_SEARCH_MODE: SEARCH_MODE_AREA,
            CONF_LOCATION: AREA_LOCATION,
            CONF_TYPE: TYPE_INPUT,
            **OPTIONAL_INPUT,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "area"

    changed = {
        **AREA_INPUT,
        CONF_OPTIONAL: {
            **OPTIONAL_INPUT,
            CONF_COUNT: 12,
            CONF_UPDATE_INTERVAL: 2,
        },
    }
    with patch(
        "custom_components.blitzerde.config_flow.BlitzerdeAPI.async_test_connection",
        new_callable=AsyncMock,
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], changed
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_COUNT] == 12
    assert result["data"][CONF_UPDATE_INTERVAL] == 2
    assert CONF_NAME not in result["data"]
    assert CONF_SEARCH_MODE not in result["data"]


async def test_route_options_menu_and_settings(hass) -> None:
    """Route settings can change without redrawing the waypoints."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Commute",
        unique_id="commute",
        data={
            CONF_NAME: "Commute",
            CONF_SEARCH_MODE: SEARCH_MODE_ROUTE,
            CONF_WAYPOINTS: [ROUTE_START, ROUTE_END],
            CONF_CORRIDOR_WIDTH: 500,
            CONF_TYPE: TYPE_INPUT,
            **OPTIONAL_INPUT,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        entry.entry_id
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "route_settings"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "route_settings"

    changed = {
        **ROUTE_OPTIONS_INPUT,
        CONF_CORRIDOR_WIDTH: 750,
    }
    with patch(
        "custom_components.blitzerde.config_flow.BlitzerdeAPI.async_test_connection",
        new_callable=AsyncMock,
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], changed
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_CORRIDOR_WIDTH] == 750
    assert result["data"][CONF_WAYPOINTS] == [
        ROUTE_START,
        ROUTE_END,
    ]
