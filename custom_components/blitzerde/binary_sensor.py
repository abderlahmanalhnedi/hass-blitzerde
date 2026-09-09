"""Binary sensor platform for Blitzer.de."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN
from .coordinator import BlitzerdeCoordinator
from .item_utils import BlitzerItem

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one binary sensor slot per configured camera position."""
    coordinator: BlitzerdeCoordinator = entry.runtime_data
    async_add_entities(
        [
            BlitzerHealthBinarySensor(
                coordinator, entry
            ),
            *[
                BlitzerMapBinarySensor(
                    coordinator, entry, index
                )
                for index in range(
                    coordinator.sensorcount
                )
            ],
        ]
    )


class BlitzerHealthBinarySensor(
    CoordinatorEntity[BlitzerdeCoordinator],
    BinarySensorEntity,
):
    """Connectivity/health entity for the upstream service."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Upstream service"

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{DOMAIN}-"
            f"{coordinator.displayname}-health"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Blitzer.de {coordinator.displayname}",
            manufacturer="Blitzer.de / atudo.net",
            model="Cloud map service",
        )

    @property
    def is_on(self) -> bool:
        """Return whether the last update completed successfully."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose useful troubleshooting telemetry."""
        return {
            "last_successful_update": (
                self.coordinator.last_successful_update.isoformat()
                if self.coordinator.last_successful_update
                else None
            ),
            "last_update_duration_ms": (
                self.coordinator.last_update_duration_ms
            ),
            "consecutive_failures": (
                self.coordinator.consecutive_failures
            ),
            "update_interval_minutes": (
                self.coordinator.update_interval_minutes
            ),
            "search_mode": self.coordinator.search_mode,
        }


class BlitzerMapBinarySensor(
    CoordinatorEntity[BlitzerdeCoordinator],
    BinarySensorEntity,
):
    """Expose one of the nearest currently reported cameras."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
        item_index: int,
    ) -> None:
        super().__init__(coordinator)
        self._item_index = item_index
        self._attr_name = (
            f"Speed camera {item_index + 1}"
        )
        self._attr_unique_id = (
            f"{DOMAIN}-"
            f"{coordinator.displayname}-"
            f"map{item_index + 1}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=(
                f"Blitzer.de "
                f"{coordinator.displayname}"
            ),
            manufacturer="Blitzer.de / atudo.net",
            model="Cloud map service",
        )

    @property
    def available(self) -> bool:
        """Expose only slots that currently contain a camera report."""
        return super().available and _camera_slot_assigned(
            self.coordinator, self._item_index
        )

    @property
    def is_on(self) -> bool:
        """Return True when a camera is assigned to this slot."""
        return _camera_slot_assigned(
            self.coordinator, self._item_index
        )

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return details for the camera assigned to this slot."""
        if not _camera_slot_assigned(
            self.coordinator, self._item_index
        ):
            return {}
        return BlitzerItem.get_attributes(
            self.coordinator.data.mapdata[
                self._item_index
            ]
        )


def _camera_slot_assigned(
    coordinator: BlitzerdeCoordinator,
    item_index: int,
) -> bool:
    """Return whether a configured binary-sensor slot has live data."""
    data = getattr(coordinator, "data", None)
    mapdata = getattr(data, "mapdata", None)
    return isinstance(mapdata, list) and len(mapdata) > item_index
