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

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise."""
        self._session = async_get_clientsession(hass)
        self.connected: bool = False

    async def _request(self, url):
        try:
            async with self._session.get(url=url) as response:
                response.raise_for_status()
                if await response.text() == "":
                    raise APIConnectionError("Empty response.")
                return await response.json()
        except ClientError as exc:
            raise APIConnectionError("Unknown error.")

    async def _requestPois(self, low_lat: float, low_ng: float, high_lat: float, high_lng: float, types: list[str] = ['ts','0','1','2','3','4','5','6']):
        pois_type = ','.join(types)
        url = f"https://cdn2.atudo.net/api/4.0/pois.php?type=ts,0,1,2,3,4,5,6&box={low_lat},{low_ng},{high_lat},{high_lng}"
        response_data = await self._request(url)
        self.connected = True
        return response_data['pois']

    async def getArea(self, latitude: float, longitude: float, radius: float):
        """get map data from api."""
        rad = radius / 100000
        high_lat = latitude + rad
        high_lng = longitude + rad
        low_lat = latitude - rad
        low_ng = longitude - rad
        #TODO: rewrite this ugly mess (but it works)
        resultAreas = []
        areas = await self._requestPois(high_lat=high_lat, high_lng=high_lng, low_lat=low_lat, low_ng=low_ng)
        for area in areas:
            if area['type'] == 'cluster':
                lat = area['lat']
                lng = area['lng']
                resultAreas = resultAreas + await self.getArea(lat, lng, radius / 10)
            else:
                areaExists = False
                for forArea in resultAreas:
                    if forArea['backend'] == area['backend']:
                        areaExists = True
                if not areaExists:
                    resultAreas.append(area)
        return resultAreas


class APIConnectionError(Exception):
    """Exception class for connection error."""
