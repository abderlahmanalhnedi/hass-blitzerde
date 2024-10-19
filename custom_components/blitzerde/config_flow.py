import voluptuous as vol
import logging

from homeassistant.config_entries import (
    ConfigFlow,
    OptionsFlowWithConfigEntry,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientError, ClientResponseError, ClientSession
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import DOMAIN

from homeassistant.const import (
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR
)

_LOGGER = logging.getLogger(__name__)

class BlitzerdeConfigFlow(ConfigFlow, domain=DOMAIN):
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for Met."""
        return BlitzerdeOptionsFlow(config_entry)


class BlitzerdeOptionsFlow(OptionsFlowWithConfigEntry):

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Configure options for Met."""

        if user_input is not None:
            # Update config entry with data from user input
            user_input[CONF_NAME] = self.config_entry.data.get(CONF_NAME)
            user_input[CONF_LOCATION] = self.config_entry.data.get(CONF_LOCATION)
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=user_input
            )
            return self.async_create_entry(
                title=self._config_entry.title, data=user_input
            )

        data_schema = {
            vol.Required(CONF_SELECTOR, default=self.config_entry.data.get(CONF_SELECTOR)): str
        }
        return self.async_show_form(step_id="init", data_schema=vol.Schema(data_schema))
