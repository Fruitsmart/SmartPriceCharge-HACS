"""Switch für SmartPriceCharge."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SmartPriceActiveSwitch(coordinator, entry)])

class SmartPriceActiveSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_has_entity_name = True
        self._attr_name = "Automatik"
        self._attr_unique_id = f"{entry.entry_id}_switch_active"
        self._attr_icon = "mdi:power"
    
    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.entry.entry_id)}, "name": "SmartPriceCharge", "manufacturer": "Custom"}

    @property
    def is_on(self): return self.coordinator.is_active

    async def async_turn_on(self, **kwargs):
        self.coordinator.is_active = True
        self.coordinator.async_set_updated_data(self.coordinator.data)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self.coordinator.is_active = False
        self.coordinator.async_set_updated_data(self.coordinator.data)
        self.async_write_ha_state()