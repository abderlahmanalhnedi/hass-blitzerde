import voluptuous as vol
import logging

from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientError, ClientResponseError, ClientSession

from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import selector

from .const import DOMAIN, CONF_HIGH_LAT, CONF_HIGH_LNG, CONF_LOW_LAT, CONF_LOW_LNG

from homeassistant.const import (
    CONF_LOCATION
)

_LOGGER = logging.getLogger(__name__)

class SmartmeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
  
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            if user_input == {}:
                return self.async_abort(reason="location")
            
            websession = async_get_clientsession(self.hass)
            
            latitude = user_input[CONF_LOCATION]['latitude']
            longitude = user_input[CONF_LOCATION]['longitude']
            radius = user_input[CONF_LOCATION]['radius']
            radius_conv = radius / 100000
            
            data = {}
            data[CONF_HIGH_LAT] = latitude + radius_conv
            data[CONF_HIGH_LNG] = longitude + radius_conv
            data[CONF_LOW_LAT] = latitude - radius_conv
            data[CONF_LOW_LNG] = longitude - radius_conv
            return self.async_create_entry(title=f"{latitude}, {longitude}, {radius}", data=data)

        data_schema = {}
        data_schema[CONF_LOCATION] = selector({
            "location": {
                "radius": True
            }
        })

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))
