"""Sensor platform for Blitzer.de."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
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
from homeassistant.util import slugify

from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_DISTANCE_KM,
    DOMAIN,
    SEARCH_MODE_ROUTE,
)
from .coordinator import BlitzerdeCoordinator
from .item_utils import BlitzerItem

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Blitzer.de sensors."""
    coordinator: BlitzerdeCoordinator = entry.runtime_data
    async_add_entities(
        [
            BlitzerCountSensor(
                coordinator, entry
            ),
            BlitzerLatestSensor(
                coordinator, entry
            ),
            BlitzerNearestSensor(
                coordinator, entry
            ),
            BlitzerLastUpdateSensor(
                coordinator, entry
            ),
            BlitzerNewCountSensor(
                coordinator, entry
            ),
        ]
    )


class BlitzerSensorEntity(
    CoordinatorEntity[BlitzerdeCoordinator],
    SensorEntity,
):
    """Base class for Blitzer.de sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=(
                f"Blitzer.de "
                f"{coordinator.displayname}"
            ),
            manufacturer="Blitzer.de / atudo.net",
            model="Cloud map service",
        )


class BlitzerCountSensor(BlitzerSensorEntity):
    """Number of exposed camera slots currently active."""

    _attr_icon = "mdi:counter"
    _attr_name = "Detected speed cameras"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{DOMAIN}-"
            f"{coordinator.displayname}-total"
        )

    @property
    def native_value(self) -> int:
        """Return the number of currently exposed camera entities."""
        return min(
            len(self.coordinator.data.mapdata),
            self.coordinator.sensorcount,
        )

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return useful aggregate information."""
        city_counts: dict[str, int] = {}
        for mapitem in self.coordinator.data.mapdata:
            address = mapitem.get("address")
            if not isinstance(address, dict):
                address = {}
            city = str(
                address.get("city") or "Unknown"
            )
            city_counts[city] = (
                city_counts.get(city, 0) + 1
            )
        return {
            "total_detected": len(
                self.coordinator.data.mapdata
            ),
            "entity_limit": (
                self.coordinator.sensorcount
            ),
            "by_city": city_counts,
            "new": self.coordinator.new_count,
            "new_minutes": self.coordinator.new_minutes,
            "ignored": len(self.coordinator.blacklist_ids),
            "last_successful_update": (
                self.coordinator.last_successful_update.isoformat()
                if self.coordinator.last_successful_update
                else None
            ),
            "last_update_duration_ms": (
                self.coordinator.last_update_duration_ms
            ),
            "service_online": (
                self.coordinator.last_update_success
            ),
            ATTR_CONFIG_ENTRY_ID: self._entry.entry_id,
            "blitzerde_source": (
                f"{DOMAIN}_{slugify(self.coordinator.displayname)}"
            ),
            "search_mode": self.coordinator.search_mode,
            "corridor_width": (
                self.coordinator.corridor_width
                if self.coordinator.search_mode == SEARCH_MODE_ROUTE
                else None
            ),
        }


class BlitzerLatestSensor(BlitzerSensorEntity):
    """Latest-looking upstream camera identifier."""

    _attr_icon = "mdi:car"
    _attr_name = "Latest speed camera"

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{DOMAIN}-"
            f"{coordinator.displayname}-latest"
        )

    @property
    def _latest_item(
        self,
    ) -> dict[str, Any] | None:
        if not self.coordinator.data.mapdata:
            return None
        return max(
            self.coordinator.data.mapdata,
            key=lambda item: str(
                item.get("backend", "")
            ),
        )

    @property
    def native_value(self) -> str | None:
        """Return the backend ID or None when no camera exists."""
        if (item := self._latest_item) is None:
            return None
        return BlitzerItem.get_backend_id(item)

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return camera details."""
        if (item := self._latest_item) is None:
            return {}
        return BlitzerItem.get_attributes(
            item, include_location=False
        )


class BlitzerNearestSensor(BlitzerSensorEntity):
    """Distance to the nearest reported camera."""

    _attr_icon = "mdi:map-marker-distance"
    _attr_name = "Nearest speed camera"
    _attr_native_unit_of_measurement = "km"

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{DOMAIN}-"
            f"{coordinator.displayname}-nearest"
        )

    @property
    def _nearest_item(
        self,
    ) -> dict[str, Any] | None:
        if not self.coordinator.data.mapdata:
            return None
        return self.coordinator.data.mapdata[0]

    @property
    def native_value(self) -> float | None:
        """Return distance in km to the nearest camera."""
        if (item := self._nearest_item) is None:
            return None
        value = item.get(ATTR_DISTANCE_KM)
        return (
            float(value)
            if value is not None
            else None
        )

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return nearest camera details."""
        if (item := self._nearest_item) is None:
            return {}
        return BlitzerItem.get_attributes(item)


class BlitzerLastUpdateSensor(BlitzerSensorEntity):
    """Timestamp of the last successful upstream refresh."""

    _attr_icon = "mdi:update"
    _attr_name = "Last successful update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{DOMAIN}-"
            f"{coordinator.displayname}-last-update"
        )

    @property
    def native_value(self):
        """Return the most recent successful coordinator update."""
        return self.coordinator.last_successful_update

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return lightweight refresh telemetry."""
        return {
            "duration_ms": self.coordinator.last_update_duration_ms,
            "consecutive_failures": (
                self.coordinator.consecutive_failures
            ),
            "update_interval_minutes": (
                self.coordinator.update_interval_minutes
            ),
        }


class BlitzerNewCountSensor(BlitzerSensorEntity):
    """Number of reports inside the configured freshness window."""

    _attr_icon = "mdi:new-box"
    _attr_name = "New speed cameras"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{DOMAIN}-"
            f"{coordinator.displayname}-new"
        )

    @property
    def native_value(self) -> int:
        """Return the number of currently fresh reports."""
        return self.coordinator.new_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the active freshness window."""
        return {
            "new_minutes": self.coordinator.new_minutes,
            "enabled": self.coordinator.new_minutes > 0,
        }
