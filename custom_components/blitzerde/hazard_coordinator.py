"""Independent traffic-hazard coordinator for Blitzer.de."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HAZARD_BLACKLIST,
    CONF_HAZARD_COUNT,
    CONF_HAZARD_NEW_MINUTES,
    CONF_HAZARD_SELECTOR,
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


class BlitzerdeHazardCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Maintain traffic hazards independently from camera refreshes.

    The coordinator is manual-only until a user explicitly opts into background
    hazard polling. Keeping the data channel separate prevents dense traffic
    layers from consuming the camera coordinator's request budget and gives us
    a stable runtime surface for map entities, events and future polling UI.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        camera_coordinator: BlitzerdeCoordinator,
    ) -> None:
        """Initialize the hazard data channel."""
        super().__init__(
            hass,
            logger=camera_coordinator.logger,
            name=f"{DOMAIN}_{camera_coordinator.displayname}_hazards",
            update_interval=None,
        )
        self.camera_coordinator = camera_coordinator
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
            raise UpdateFailed(f"Could not update traffic hazards: {err}") from err
