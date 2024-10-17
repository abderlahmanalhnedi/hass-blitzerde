import voluptuous as vol
import logging

from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientError, ClientResponseError, ClientSession

from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import selector

from .const import DOMAIN

from homeassistant.const import (
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR
)

_LOGGER = logging.getLogger(__name__)

class SmartmeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            if user_input == {}: #default location
                return self.async_abort(reason="location")

            return self.async_create_entry(title=f"Blitzer.de {user_input[CONF_NAME]}", data=user_input)

        data_schema = {
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_SELECTOR, default="(Stadt1)|(Stadt2)"): str
        }
        data_schema[CONF_LOCATION] = selector({
            "location": {
                "radius": True
            }
        })

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))
