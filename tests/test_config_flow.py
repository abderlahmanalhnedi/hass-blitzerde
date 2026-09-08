"""Runtime tests for the Blitzer.de config and options flows."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
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
from homeassistant.util import slugify
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

pytestmark = pytest.mark.asyncio

AREA_LOCATION = {
    "latitude": 51.0504,
    "longitude": 13.7373,
    "radius": 1500,
}
WAYPOINT_1 = {
    "latitude": 51.0504,
    "longitude": 13.7373,
}
WAYPOINT_2 = {
    "latitude": 51.0604,
    "longitude": 13.7573,
}
TYPES = {
    "mobile": True,
    "trailer": True,
    "fixed": False,
}
OPTIONAL = {
    CONF_COUNT: 9,
    CONF_SELECTOR: ".*",
    CONF_CONDITION: True,
    CONF_UPDATE_INTERVAL: 1,
    CONF_NEW_MINUTES: 60,
    CONF_BLACKLIST: "",
}


@pytest.fixture
def mock_setup_entry():
    """Prevent config-flow tests from setting up platforms."""
    with patch(
        "custom_components.blitzerde.async_setup_entry",
        AsyncMock(return_value=True),
    ) as mocked:
        yield mocked


async def _start_area_flow(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Dresden",
            CONF_SEARCH_MODE: SEARCH_MODE_AREA,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "area"
    return result


@pytest.mark.usefixtures("mock_setup_entry")
async def test_area_flow_success(hass) -> None:
    """Test the complete area setup flow."""
    result = await _start_area_flow(hass)

    with patch(
        "custom_components.blitzerde.config_flow._async_test_area_connection",
        AsyncMock(return_value=None),
    ) as test_connection:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LOCATION: AREA_LOCATION,
                CONF_TYPE: TYPES,
                CONF_OPTIONAL: OPTIONAL,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Blitzer.de Dresden"
    assert result["data"][CONF_SEARCH_MODE] == SEARCH_MODE_AREA
    assert result["data"][CONF_LOCATION] == AREA_LOCATION
    test_connection.assert_awaited_once()


@pytest.mark.usefixtures("mock_setup_entry")
async def test_area_flow_recovers_after_connection_error(hass) -> None:
    """Test that a failed connection can be corrected without restarting."""
    result = await _start_area_flow(hass)
    values = {
        CONF_LOCATION: AREA_LOCATION,
        CONF_TYPE: TYPES,
        CONF_OPTIONAL: OPTIONAL,
    }

    with patch(
        "custom_components.blitzerde.config_flow._async_test_area_connection",
        AsyncMock(
            side_effect=[
                APIConnectionError("temporary outage"),
                None,
            ]
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            values,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            values,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.usefixtures("mock_setup_entry")
async def test_area_flow_rejects_invalid_filter_before_network(hass) -> None:
    """Test local validation happens before any upstream request."""
    result = await _start_area_flow(hass)
    bad_optional = {
        **OPTIONAL,
        CONF_SELECTOR: "[broken",
    }

    connection = AsyncMock(return_value=None)
    with patch(
        "custom_components.blitzerde.config_flow._async_test_area_connection",
        connection,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LOCATION: AREA_LOCATION,
                CONF_TYPE: TYPES,
                CONF_OPTIONAL: bad_optional,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_regex"}
    connection.assert_not_awaited()


@pytest.mark.usefixtures("mock_setup_entry")
async def test_duplicate_name_is_rejected(hass) -> None:
    """Test duplicate config entries are stopped at the first step."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        unique_id=slugify("Dresden"),
        data={
            CONF_NAME: "Dresden",
            CONF_SEARCH_MODE: SEARCH_MODE_AREA,
            CONF_LOCATION: AREA_LOCATION,
        },
        version=8,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Dresden",
            CONF_SEARCH_MODE: SEARCH_MODE_AREA,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_route_flow_success(hass) -> None:
    """Test the complete waypoint route flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Commute",
            CONF_SEARCH_MODE: SEARCH_MODE_ROUTE,
        },
    )
    assert result["step_id"] == "waypoint"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: WAYPOINT_1,
            "add_another": True,
        },
    )
    assert result["step_id"] == "waypoint"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: WAYPOINT_2,
            "add_another": False,
        },
    )
    assert result["step_id"] == "route_options"

    with patch(
        "custom_components.blitzerde.config_flow._async_test_route_connection",
        AsyncMock(return_value=None),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CORRIDOR_WIDTH: 500,
                CONF_TYPE: TYPES,
                CONF_OPTIONAL: OPTIONAL,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SEARCH_MODE] == SEARCH_MODE_ROUTE
    assert result["data"][CONF_WAYPOINTS] == [
        WAYPOINT_1,
        WAYPOINT_2,
    ]
    assert result["data"][CONF_CORRIDOR_WIDTH] == 500


async def test_area_options_flow(hass) -> None:
    """Test mutable area settings are stored as options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Blitzer.de Dresden",
        unique_id="dresden",
        data={
            CONF_NAME: "Dresden",
            CONF_SEARCH_MODE: SEARCH_MODE_AREA,
            CONF_LOCATION: AREA_LOCATION,
            CONF_TYPE: TYPES,
            **OPTIONAL,
        },
        version=8,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        entry.entry_id
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "area"

    changed_location = {
        **AREA_LOCATION,
        "radius": 2500,
    }
    with patch(
        "custom_components.blitzerde.config_flow._async_test_area_connection",
        AsyncMock(return_value=None),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_LOCATION: changed_location,
                CONF_TYPE: TYPES,
                CONF_OPTIONAL: {
                    **OPTIONAL,
                    CONF_UPDATE_INTERVAL: 2,
                },
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_LOCATION] == changed_location
    assert result["data"][CONF_UPDATE_INTERVAL] == 2
