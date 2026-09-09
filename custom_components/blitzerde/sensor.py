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
from .hazard_coordinator import BlitzerdeHazardCoordinator
from .item_utils import BlitzerItem

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Blitzer.de sensors."""
    coordinator: BlitzerdeCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        BlitzerCountSensor(coordinator, entry),
        BlitzerLatestSensor(coordinator, entry),
        BlitzerNearestSensor(coordinator, entry),
        BlitzerLastUpdateSensor(coordinator, entry),
        BlitzerNewCountSensor(coordinator, entry),
    ]

    hazard_coordinator = getattr(coordinator, "hazard_coordinator", None)
    if isinstance(hazard_coordinator, BlitzerdeHazardCoordinator):
        entities.extend(
            [
                BlitzerHazardCountSensor(hazard_coordinator, entry),
                BlitzerNearestHazardSensor(hazard_coordinator, entry),
                BlitzerNewHazardCountSensor(hazard_coordinator, entry),
            ]
        )

    async_add_entities(entities)


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
        self._attr_device_info = _device_info(entry, coordinator.displayname)


class BlitzerHazardSensorEntity(
    CoordinatorEntity[BlitzerdeHazardCoordinator],
    SensorEntity,
):
    """Base class for sensors backed by the independent hazard channel."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BlitzerdeHazardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = _device_info(
            entry,
            coordinator.camera_coordinator.displayname,
        )

    @property
    def available(self) -> bool:
        """Return unavailable when hazard monitoring is not enabled."""
        return super().available and _hazard_channel_enabled(
            self.coordinator.enabled_types
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
        self._attr_unique_id = f"{DOMAIN}-{coordinator.displayname}-total"

    @property
    def native_value(self) -> int:
        """Return the number of currently exposed camera entities."""
        return min(
            len(self.coordinator.data.mapdata),
            self.coordinator.sensorcount,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful aggregate information."""
        city_counts: dict[str, int] = {}
        for mapitem in self.coordinator.data.mapdata:
            address = mapitem.get("address")
            if not isinstance(address, dict):
                address = {}
            city = str(address.get("city") or "Unknown")
            city_counts[city] = city_counts.get(city, 0) + 1
        return {
            "total_detected": len(self.coordinator.data.mapdata),
            "entity_limit": self.coordinator.sensorcount,
            "by_city": city_counts,
            "new": self.coordinator.new_count,
            "new_minutes": self.coordinator.new_minutes,
            "ignored": len(self.coordinator.blacklist_ids),
            "last_successful_update": (
                self.coordinator.last_successful_update.isoformat()
                if self.coordinator.last_successful_update
                else None
            ),
            "last_update_duration_ms": self.coordinator.last_update_duration_ms,
            "service_online": self.coordinator.last_update_success,
            ATTR_CONFIG_ENTRY_ID: self._entry.entry_id,
            "blitzerde_source": f"{DOMAIN}_{slugify(self.coordinator.displayname)}",
            "search_mode": self.coordinator.search_mode,
            "corridor_width": (
                self.coordinator.corridor_width
                if self.coordinator.search_mode == SEARCH_MODE_ROUTE
                else None
            ),
        }


class BlitzerLatestSensor(BlitzerSensorEntity):
    """Most recently reported camera with a user-friendly state."""

    _attr_icon = "mdi:car"
    _attr_name = "Latest speed camera"

    def __init__(
        self,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}-{coordinator.displayname}-latest"

    @property
    def _latest_item(self) -> dict[str, Any] | None:
        return _latest_camera_item(self.coordinator.data.mapdata)

    @property
    def native_value(self) -> str | None:
        """Return a readable location/description for the latest camera."""
        if (item := self._latest_item) is None:
            return None
        return _camera_display_name(item)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return camera details."""
        if (item := self._latest_item) is None:
            return {}
        return BlitzerItem.get_attributes(item, include_location=False)


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
        self._attr_unique_id = f"{DOMAIN}-{coordinator.displayname}-nearest"

    @property
    def _nearest_item(self) -> dict[str, Any] | None:
        if not self.coordinator.data.mapdata:
            return None
        return self.coordinator.data.mapdata[0]

    @property
    def native_value(self) -> float | None:
        """Return distance in km to the nearest camera."""
        if (item := self._nearest_item) is None:
            return None
        value = item.get(ATTR_DISTANCE_KM)
        return float(value) if value is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
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
        self._attr_unique_id = f"{DOMAIN}-{coordinator.displayname}-last-update"

    @property
    def native_value(self):
        """Return the most recent successful coordinator update."""
        return self.coordinator.last_successful_update

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return lightweight refresh telemetry."""
        return {
            "duration_ms": self.coordinator.last_update_duration_ms,
            "consecutive_failures": self.coordinator.consecutive_failures,
            "update_interval_minutes": self.coordinator.update_interval_minutes,
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
        self._attr_unique_id = f"{DOMAIN}-{coordinator.displayname}-new"

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


class BlitzerHazardCountSensor(BlitzerHazardSensorEntity):
    """Number of currently exposed traffic hazards."""

    _attr_icon = "mdi:alert-circle-outline"
    _attr_name = "Traffic hazards"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BlitzerdeHazardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}-{entry.entry_id}-hazards-total"

    @property
    def native_value(self) -> int:
        """Return the number of hazards currently retained by the coordinator."""
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return aggregate hazard information suitable for dashboards."""
        by_kind: dict[str, int] = {}
        for item in self.coordinator.data or []:
            kind = str(item.get("hazard_kind") or "unknown")
            by_kind[kind] = by_kind.get(kind, 0) + 1
        return {
            "by_kind": by_kind,
            "enabled_types": self.coordinator.enabled_types,
            "entity_limit": self.coordinator.count,
            "background_polling": self.coordinator.background_polling_enabled,
            ATTR_CONFIG_ENTRY_ID: self._entry.entry_id,
        }


class BlitzerNearestHazardSensor(BlitzerHazardSensorEntity):
    """Distance to the nearest traffic hazard."""

    _attr_icon = "mdi:map-marker-alert-outline"
    _attr_name = "Nearest traffic hazard"
    _attr_native_unit_of_measurement = "km"

    def __init__(
        self,
        coordinator: BlitzerdeHazardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}-{entry.entry_id}-hazards-nearest"

    @property
    def _nearest_item(self) -> dict[str, Any] | None:
        data = self.coordinator.data or []
        return data[0] if data else None

    @property
    def native_value(self) -> float | None:
        """Return distance in km to the nearest normalized hazard."""
        if (item := self._nearest_item) is None:
            return None
        value = item.get(ATTR_DISTANCE_KM)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the normalized nearest-hazard details."""
        if (item := self._nearest_item) is None:
            return {}
        address = item.get("address")
        if not isinstance(address, dict):
            address = {}
        return {
            "hazard_kind": item.get("hazard_kind"),
            "summary": item.get("summary"),
            "city": address.get("city"),
            "street": address.get("street"),
            "latitude": item.get("lat"),
            "longitude": item.get("lng"),
            "new": bool(item.get("new", False)),
            "age_minutes": item.get("age_minutes"),
            ATTR_CONFIG_ENTRY_ID: self._entry.entry_id,
        }


class BlitzerNewHazardCountSensor(BlitzerHazardSensorEntity):
    """Number of traffic hazards inside the configured freshness window."""

    _attr_icon = "mdi:alert-decagram-outline"
    _attr_name = "New traffic hazards"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BlitzerdeHazardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}-{entry.entry_id}-hazards-new"

    @property
    def native_value(self) -> int:
        """Return the number of normalized hazards marked as new."""
        return sum(1 for item in self.coordinator.data or [] if item.get("new"))



def _latest_camera_item(
    items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return the freshest camera, preferring normalized report age."""
    if not items:
        return None

    aged: list[tuple[float, dict[str, Any]]] = []
    for item in items:
        try:
            age = float(item["age_minutes"])
        except (KeyError, TypeError, ValueError):
            continue
        aged.append((age, item))

    if aged:
        return min(aged, key=lambda pair: pair[0])[1]

    return max(
        items,
        key=lambda item: str(item.get("backend", "")),
    )


def _camera_display_name(item: dict[str, Any]) -> str:
    """Return a compact human-readable camera label for entity state."""
    attrs = BlitzerItem.get_attributes(item, include_location=False)
    street = str(attrs.get("street") or "").strip()
    city = str(attrs.get("city") or "").strip()

    if street and city:
        return f"{street}, {city}"
    if street:
        return street
    if city:
        return city

    description = str(attrs.get("description") or "").strip()
    if description:
        return description

    return f"Camera {BlitzerItem.get_backend_id(item)}"


def _hazard_channel_enabled(enabled_types: list[str]) -> bool:
    """Return whether hazard monitoring has at least one selected type."""
    return bool(enabled_types)
def _device_info(entry: ConfigEntry, displayname: str) -> DeviceInfo:
    """Return one shared device identity for camera and hazard sensors."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Blitzer.de {displayname}",
        manufacturer="Blitzer.de / atudo.net",
        model="Cloud map service",
    )
