from dataclasses import dataclass
from datetime import timedelta
import logging

import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import API
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class BlitzerdeAPIData:
    """Class to hold api data."""

    mapdata: [any]


class BlitzerdeCoordinator(DataUpdateCoordinator):
    """My coordinator."""

    data: BlitzerdeAPIData

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow setup
        self.location = config_entry.data[CONF_LOCATION]
        self.displayname = config_entry.data[CONF_NAME]
        self.whitelist = config_entry.data[CONF_SELECTOR]

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=60),
        )

        # Initialise your api here
        self.api = API(hass, latitude=self.location['latitude'], longitude=self.location['longitude'], radius=self.location['radius'])

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            mapdata = await self.api.pullMapData()
            filtered_list = list(
                filter(
                    lambda mapitem: re.match(self.whitelist, mapitem['address']['city']),
                    mapdata
                )
            )
            return BlitzerdeAPIData(mapdata=filtered_list)
        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err
