"""Blitzerde coordinator module."""
from __future__ import annotations
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import BlitzerdeApiClient

_LOGGER = logging.getLogger(__name__)

class BlitzerdeCoordinator(DataUpdateCoordinator):
    """Koordinator für Blitzerde Daten."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BlitzerdeApiClient,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="blitzerde",
            update_interval=timedelta(seconds=30),
        )
        self.client = client

    async def _async_update_data(self):
        """Hole aktuelle Blitzerde Daten."""
        try:
            # Debug logging für rohe API Daten
            data = await self.client.async_get_data()
            _LOGGER.debug("Rohe API Daten: %s", data)

            if not data:
                _LOGGER.warning("Keine Daten von der API erhalten")
                return None

            # Filtere bestätigte Einträge
            mapdata = list(
                filter(
                    lambda mapitem: mapitem.get('info', {}).get('confirmed', 0) == 1,
                    data
                )
            )
            
            return mapdata

        except KeyError as err:
            _LOGGER.error("Fehler beim Zugriff auf Datenstruktur: %s", err)
            return None
        except Exception as err:
            _LOGGER.error("Unerwarteter Fehler beim Update der Daten: %s", err)
            return Nonefrom dataclasses import dataclass
from datetime import timedelta
import logging

import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LOCATION,
    CONF_NAME,
    CONF_COUNT,
    CONF_TYPE,
    CONF_SELECTOR,
    CONF_CONDITION
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BlitzerdeAPI, APIConnectionError
from .const import DOMAIN

from .const import (
    TYPE_TRAILER,
    TYPE_MOBILE,
    TYPE_FIXED
)

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
        self.sensorcount = config_entry.data[CONF_COUNT]
        self.types = config_entry.data[CONF_TYPE]
        self.only_confirmed = config_entry.data[CONF_CONDITION]

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
        self.api = BlitzerdeAPI(hass)

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            types = []
            if self.types['mobile']:
                types = types + TYPE_MOBILE
            if self.types['trailer']:
                types = types + TYPE_TRAILER
            if self.types['fixed']:
                types = types + TYPE_FIXED

            mapdata = await self.api.getArea(latitude=self.location['latitude'], longitude=self.location['longitude'], radius=self.location['radius'], types=types)
            mapdata = list(
                filter(
                    lambda mapitem: re.match(self.whitelist, mapitem['address']['city']),
                    mapdata
                )
            )
            if self.only_confirmed:
                mapdata = list(
                    filter(
                        lambda mapitem: mapitem['info']['confirmed'] == 1,
                        mapdata
                    )
                )
            return BlitzerdeAPIData(mapdata=mapdata)
        except APIConnectionError as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            raise UpdateFailed(f"Error communicating with API: {err}") from err
