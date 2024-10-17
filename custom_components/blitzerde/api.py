from dataclasses import dataclass
from enum import StrEnum
import logging
from random import choice, randrange

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientError, ClientResponseError, ClientSession
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class API:
    """Class for API."""

    def __init__(self, hass: HomeAssistant, latitude: float, longitude: float, radius: float) -> None:
        """Initialise."""
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius
        self._session = async_get_clientsession(hass)
        self.connected: bool = False

    async def pullMapData(self):
        """get map data from api."""
        rad = self.radius / 100000
        high_lat = self.latitude + rad
        high_lng = self.longitude + rad
        low_lat = self.latitude - rad
        low_ng = self.longitude - rad

        try:
            url = f"https://cdn2.atudo.net/api/4.0/pois.php?type=ts,0,1,2,3,4,5,6&box={low_lat},{low_ng},{high_lat},{high_lng}"
            async with self._session.get(url=url) as response:
                response.raise_for_status()
                response_text = await response.text()
                response_data = await response.json()
                if response_text == "":
                    raise APIConnectionError("Empty response.")
                
                self.connected = True
                return response_data['pois']
        except ClientError as exc:
            raise APIConnectionError("Unknown error.")


class APIConnectionError(Exception):
    """Exception class for connection error."""
