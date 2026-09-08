"""Data update coordinator for Blitzer.de."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CONDITION,
    CONF_COUNT,
    CONF_LOCATION,
    CONF_NAME,
    CONF_SELECTOR,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import APIConnectionError, APIRateLimitError, BlitzerdeAPI
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_ONLY_CONFIRMED,
    DEFAULT_SELECTOR,
    DEFAULT_SENSOR_COUNT,
    DEFAULT_TYPES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    TYPE_FIXED,
    TYPE_MOBILE,
    TYPE_TRAILER,
)
from .item_utils import item_info

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class BlitzerdeAPIData:
    """Normalized coordinator payload."""

    mapdata: list[dict[str, Any]]


class BlitzerdeCoordinator(DataUpdateCoordinator[BlitzerdeAPIData]):
    """Fetch and normalize Blitzer.de data for one config entry."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry
    ) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self.api = BlitzerdeAPI(hass)

        interval_minutes = int(
            config_entry.options.get(
                CONF_UPDATE_INTERVAL,
                config_entry.data.get(
                    CONF_UPDATE_INTERVAL,
                    DEFAULT_UPDATE_INTERVAL_MINUTES,
                ),
            )
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}:{config_entry.entry_id}",
            update_interval=(
                None
                if interval_minutes <= 0
                else timedelta(minutes=interval_minutes)
            ),
        )

    @property
    def displayname(self) -> str:
        """Return the configured display name."""
        return str(
            self.config_entry.data.get(
                CONF_NAME, self.config_entry.title
            )
        )

    @property
    def location(self) -> dict[str, Any]:
        """Return current location options."""
        return dict(self._value(CONF_LOCATION, {}))

    @property
    def whitelist(self) -> str:
        """Return configured city regex."""
        return str(self._value(CONF_SELECTOR, DEFAULT_SELECTOR))

    @property
    def sensorcount(self) -> int:
        """Return configured number of binary/geolocation slots."""
        return int(self._value(CONF_COUNT, DEFAULT_SENSOR_COUNT))

    @property
    def update_interval_minutes(self) -> int:
        """Return the configured polling interval in minutes."""
        return int(
            self._value(
                CONF_UPDATE_INTERVAL,
                DEFAULT_UPDATE_INTERVAL_MINUTES,
            )
        )

    @property
    def types(self) -> dict[str, bool]:
        """Return enabled camera types."""
        raw = self._value(CONF_TYPE, DEFAULT_TYPES)
        return {
            key: bool(raw.get(key, default))
            for key, default in DEFAULT_TYPES.items()
        }

    @property
    def only_confirmed(self) -> bool:
        """Return whether only confirmed reports should be included."""
        return bool(
            self._value(
                CONF_CONDITION, DEFAULT_ONLY_CONFIRMED
            )
        )

    def _value(self, key: str, default: Any) -> Any:
        """Read an option first, then fall back to initial config data."""
        return self.config_entry.options.get(
            key, self.config_entry.data.get(key, default)
        )

    def enabled_types(self) -> list[int | str]:
        """Return the upstream type identifiers selected by the user."""
        selected: list[int | str] = []
        if self.types["mobile"]:
            selected.extend(TYPE_MOBILE)
        if self.types["trailer"]:
            selected.extend(TYPE_TRAILER)
        if self.types["fixed"]:
            selected.extend(TYPE_FIXED)
        return selected

    async def _async_update_data(self) -> BlitzerdeAPIData:
        """Fetch, filter and sort current camera data."""
        try:
            location = self.location
            mapdata = await self.api.async_get_area(
                latitude=float(location["latitude"]),
                longitude=float(location["longitude"]),
                radius=float(location["radius"]),
                types=self.enabled_types(),
            )
        except APIRateLimitError as err:
            raise UpdateFailed(
                retry_after=err.retry_after
            ) from err
        except (
            APIConnectionError,
            KeyError,
            TypeError,
            ValueError,
        ) as err:
            raise UpdateFailed(
                f"Error communicating with Blitzer.de: {err}"
            ) from err

        try:
            city_pattern = re.compile(self.whitelist)
        except re.error as err:
            raise UpdateFailed(
                f"Invalid city filter regular expression: {err}"
            ) from err

        filtered: list[dict[str, Any]] = []
        for item in mapdata:
            address = item.get("address")
            if not isinstance(address, dict):
                address = {}
            city = str(address.get("city") or "")
            if not city_pattern.search(city):
                continue

            if self.only_confirmed:
                info = item_info(item)
                if str(info.get("confirmed", "")) != "1":
                    continue

            filtered.append(item)

        return BlitzerdeAPIData(mapdata=filtered)
