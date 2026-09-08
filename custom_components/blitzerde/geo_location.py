"""Geolocation platform for Blitzer.de speed-camera reports."""

from __future__ import annotations

from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .const import ATTR_DISTANCE_KM, DOMAIN, EVENT_NEW_CAMERA
from .coordinator import BlitzerdeCoordinator
from .item_utils import BlitzerItem, item_info

PARALLEL_UPDATES = 0

_REDLIGHT_TYPE_CODES = {"2", "110", "111"}


def _poi_id(item: dict[str, Any]) -> str:
    """Return the public backend identifier for one POI."""
    return BlitzerItem.get_backend_id(item)


def _camera_type(item: dict[str, Any]) -> str:
    """Return a useful installation category for a POI."""
    info = item_info(item)
    if str(info.get("partly_fixed", "")) == "1":
        return "trailer"
    if str(info.get("fixed", "")) == "1":
        return "fixed"

    code = str(item.get("type", ""))
    if code.isdigit() and 100 <= int(code) < 200:
        return "fixed"
    return "mobile"


def _camera_icon(item: dict[str, Any]) -> str:
    """Return an icon that is useful outside the map card as well."""
    code = str(item.get("type", ""))
    if str(item.get("vmax", "")) == "/" or code in _REDLIGHT_TYPE_CODES:
        return "mdi:traffic-light"

    return {
        "fixed": "mdi:cctv",
        "trailer": "mdi:truck-trailer",
        "mobile": "mdi:speedometer",
    }.get(_camera_type(item), "mdi:map-marker-alert")


def _summary(item: dict[str, Any]) -> str:
    """Build a short human-readable camera summary."""
    address = item.get("address")
    if not isinstance(address, dict):
        address = {}

    parts = [
        address.get("street"),
        address.get("city"),
    ]
    place = ", ".join(str(part) for part in parts if part)

    vmax = item.get("vmax")
    if vmax not in (None, "", "?", "/"):
        return f"{place} · {vmax} km/h" if place else f"{vmax} km/h"

    if str(vmax) == "/":
        return f"{place} · red light" if place else "Red light camera"

    return place or f"Camera {_poi_id(item)}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up dynamic geolocation entities for one configured area."""
    coordinator: BlitzerdeCoordinator = entry.runtime_data
    registry = er.async_get(hass)

    known: dict[str, BlitzerdeGeoLocation] = {}
    seen_report_ids: set[str] | None = None
    unique_prefix = f"{DOMAIN}-geo-{entry.entry_id}-"

    @callback
    def _sync_entities() -> None:
        """Synchronize current POIs with Home Assistant entities."""
        nonlocal seen_report_ids

        mapdata = coordinator.data.mapdata if coordinator.data else []
        visible = mapdata[: coordinator.sensorcount]

        visible_ids = {_poi_id(item) for item in visible}
        all_ids = {_poi_id(item) for item in mapdata}

        new_entities: list[BlitzerdeGeoLocation] = []
        for item in visible:
            poi_id = _poi_id(item)
            entity = known.get(poi_id)
            if entity is None:
                entity = BlitzerdeGeoLocation(
                    coordinator=coordinator,
                    entry=entry,
                    poi_id=poi_id,
                    item=item,
                )
                known[poi_id] = entity
                new_entities.append(entity)
            else:
                entity.update_from_item(item)

        for registry_entry in list(
            er.async_entries_for_config_entry(registry, entry.entry_id)
        ):
            if registry_entry.domain != "geo_location":
                continue
            if not registry_entry.unique_id.startswith(unique_prefix):
                continue

            poi_id = registry_entry.unique_id[len(unique_prefix) :]
            if poi_id in visible_ids:
                continue

            known.pop(poi_id, None)
            registry.async_remove(registry_entry.entity_id)

        if new_entities:
            async_add_entities(new_entities)

        if seen_report_ids is None:
            seen_report_ids = set(all_ids)
        else:
            new_ids = all_ids - seen_report_ids
            if new_ids:
                by_id = {_poi_id(item): item for item in mapdata}
                for poi_id in sorted(new_ids):
                    item = by_id[poi_id]
                    payload = BlitzerItem.get_attributes(item)
                    payload.update(
                        {
                            "config_entry_id": entry.entry_id,
                            "area": coordinator.displayname,
                            "id": poi_id,
                            "camera_type": _camera_type(item),
                            "summary": _summary(item),
                        }
                    )
                    hass.bus.async_fire(EVENT_NEW_CAMERA, payload)
                seen_report_ids.update(new_ids)

    entry.async_on_unload(
        coordinator.async_add_listener(_sync_entities)
    )
    _sync_entities()


class BlitzerdeGeoLocation(GeolocationEvent):
    """Represent one reported camera on Home Assistant's map."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        *,
        coordinator: BlitzerdeCoordinator,
        entry: ConfigEntry,
        poi_id: str,
        item: dict[str, Any],
    ) -> None:
        """Initialize one camera marker."""
        self._coordinator = coordinator
        self._poi_id = poi_id
        self._attr_source = (
            f"{DOMAIN}_{slugify(coordinator.displayname)}"
        )
        self._attr_unique_id = (
            f"{DOMAIN}-geo-{entry.entry_id}-{poi_id}"
        )
        self._attr_unit_of_measurement = UnitOfLength.KILOMETERS
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Blitzer.de {coordinator.displayname}",
            manufacturer="Blitzer.de / atudo.net",
            model="Cloud map service",
        )
        self._extra_attributes: dict[str, Any] = {}
        self._apply(item)

    def _apply(self, item: dict[str, Any]) -> None:
        """Apply fresh API data to this marker."""
        address = item.get("address")
        if not isinstance(address, dict):
            address = {}

        street = address.get("street")
        city = address.get("city")
        display_place = street or city or self._poi_id

        self._attr_name = f"Speed camera {display_place}"
        self._attr_latitude = float(item["lat"])
        self._attr_longitude = float(item["lng"])
        self._attr_distance = float(
            item.get(ATTR_DISTANCE_KM, 0.0)
        )
        self._attr_icon = _camera_icon(item)
        self._attr_entity_picture = (
            "https://map.blitzer.de/v5/images/"
            f"{BlitzerItem.get_picture_path(item)}.svg"
        )

        self._extra_attributes = BlitzerItem.get_attributes(
            item, include_location=False
        )
        self._extra_attributes.update(
            {
                "id": self._poi_id,
                "camera_type": _camera_type(item),
                "summary": _summary(item),
                "area": self._coordinator.displayname,
            }
        )

    @callback
    def update_from_item(self, item: dict[str, Any]) -> None:
        """Refresh this entity after a coordinator update."""
        self._apply(item)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return camera metadata."""
        return self._extra_attributes
