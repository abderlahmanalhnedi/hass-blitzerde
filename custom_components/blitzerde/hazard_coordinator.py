"""Independent traffic-hazard coordinator for Blitzer.de."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HAZARD_BLACKLIST,
    CONF_HAZARD_COUNT,
    CONF_HAZARD_NEW_MINUTES,
    CONF_HAZARD_SELECTOR,
    CONF_HAZARD_UPDATE_INTERVAL,
    DEFAULT_HAZARD_COUNT,
    DEFAULT_NEW_MINUTES,
    DEFAULT_SELECTOR,
    DOMAIN,
)
from .coordinator import BlitzerdeCoordinator
from .hazard_runtime import (
    _csv_set,
    _value,
    async_fetch_hazards,
    configured_hazard_types,
)
from .hazards import normalize_hazards

_LOGGER = logging.getLogger(__name__)


class BlitzerdeHazardCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Maintain traffic hazards independently from camera refreshes.

    Hazard polling has its own interval and request channel. A value of ``0``
    keeps the hazard half manual-only; positive values opt the entry into
    background refreshes without changing the camera coordinator cadence.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        camera_coordinator: BlitzerdeCoordinator,
    ) -> None:
        """Initialize the hazard data channel."""
        self.camera_coordinator = camera_coordinator
        interval_minutes = int(
            _value(
                camera_coordinator,
                CONF_HAZARD_UPDATE_INTERVAL,
                0,
            )
        )
        update_interval = (
            timedelta(minutes=interval_minutes)
            if interval_minutes > 0 and configured_hazard_types(camera_coordinator)
            else None
        )

        super().__init__(
            hass,
            _LOGGER,
            name=(
                f"{DOMAIN}:"
                f"{camera_coordinator.config_entry.entry_id}:hazards"
            ),
            update_interval=update_interval,
        )
        self.data = []

    @property
    def count(self) -> int:
        """Return the configured maximum number of exposed hazards."""
        return int(
            _value(
                self.camera_coordinator,
                CONF_HAZARD_COUNT,
                DEFAULT_HAZARD_COUNT,
            )
        )

    @property
    def enabled_types(self) -> list[str]:
        """Return the hazard kinds enabled for the entry."""
        return configured_hazard_types(self.camera_coordinator)

    @property
    def background_polling_enabled(self) -> bool:
        """Return whether the entry opted into automatic hazard refreshes."""
        return self.update_interval is not None

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch and normalize the hazard half without touching cameras."""
        try:
            enabled = self.enabled_types
            raw = await async_fetch_hazards(
                self.camera_coordinator,
                enabled=enabled,
            )
            normalized = normalize_hazards(
                raw,
                enabled=enabled,
                city_filter=str(
                    _value(
                        self.camera_coordinator,
                        CONF_HAZARD_SELECTOR,
                        DEFAULT_SELECTOR,
                    )
                ),
                blacklist_ids=_csv_set(
                    _value(
                        self.camera_coordinator,
                        CONF_HAZARD_BLACKLIST,
                        "",
                    )
                ),
                new_minutes=int(
                    _value(
                        self.camera_coordinator,
                        CONF_HAZARD_NEW_MINUTES,
                        DEFAULT_NEW_MINUTES,
                    )
                ),
                now=dt_util.now(),
            )
            return normalized[: self.count]
        except Exception as err:
            raise UpdateFailed(
                f"Could not update traffic hazards: {err}"
            ) from err
