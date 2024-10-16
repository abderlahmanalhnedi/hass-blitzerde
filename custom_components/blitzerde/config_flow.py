import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientError, ClientResponseError, ClientSession, BasicAuth

from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import selector

from .const import DOMAIN

class SmartmeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
  
    async def async_step_user(self, user_input=None):
        # Specify items in the order they are to be displayed in the UI
        data_schema = {
            "select_location": selector({
                "location": {}
            })
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(data_schema))
