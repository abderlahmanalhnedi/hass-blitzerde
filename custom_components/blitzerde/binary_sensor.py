import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    STATE_ON,
    STATE_OFF,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BlitzerdeCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: BlitzerdeCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ].coordinator

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = [
        # 0 to 9 for sorting in ha
        MapBinarySensor(coordinator, 0),
        MapBinarySensor(coordinator, 1),
        MapBinarySensor(coordinator, 2),
        MapBinarySensor(coordinator, 3),
        MapBinarySensor(coordinator, 4),
        MapBinarySensor(coordinator, 5),
        MapBinarySensor(coordinator, 6),
        MapBinarySensor(coordinator, 7),
        MapBinarySensor(coordinator, 8),
    ]

    # Create the sensors.
    async_add_entities(sensors)

class MapBinarySensor(CoordinatorEntity):
    
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    
    def __init__(self, coordinator: BlitzerdeCoordinator, itemid: int) -> None:
        super().__init__(coordinator)
        self._itemid = itemid
        self.name = f"Blitzer {self.coordinator.displayname} {self._itemid+1}"
        self.unique_id = f"{DOMAIN}-{self.coordinator.displayname}-map{self._itemid+1}"

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return len(self.coordinator.data.mapdata) > self._itemid
    
    @property
    def state(self):
        return STATE_ON if self.is_on else STATE_OFF

    @property
    def extra_state_attributes(self):
        if not self.is_on:
            return {}
        
        item = self.coordinator.data.mapdata[self._itemid]
        attrs = {}
        attrs[ATTR_LATITUDE] = item['lat']
        attrs[ATTR_LONGITUDE] = item['lng']
        attrs['vmax'] = item['vmax']
        attrs['counter'] = item['counter']
        attrs['city'] = item['address']['city']
        attrs['street'] = item['address']['street']
        attrs['zip_code'] = item['address']['zip_code']
        return attrs
