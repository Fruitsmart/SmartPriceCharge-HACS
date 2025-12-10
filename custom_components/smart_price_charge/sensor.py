"""Sensoren für SmartPriceCharge."""
from homeassistant.components.sensor import (
    SensorEntity, SensorDeviceClass, SensorStateClass
)
from homeassistant.const import UnitOfEnergy, CURRENCY_EURO
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SmartPriceStatusSensor(coordinator, entry),
        SmartPriceModeSensor(coordinator, entry),
        SmartPriceSessionSensor(coordinator, entry),
        SmartPriceCurrentPriceSensor(coordinator, entry),
        SmartPricePeakPriceSensor(coordinator, entry),
        SmartPricePeakTimeSensor(coordinator, entry),
        SmartPriceNextChargeSensor(coordinator, entry),
        SmartPriceSlotsInfoSensor(coordinator, entry),
        # Kosten
        SmartPriceCostTotalSensor(coordinator, entry),
        SmartPriceSavingsTotalSensor(coordinator, entry),
        SmartPriceDischargeSavingsTotalSensor(coordinator, entry),
        SmartPricePVSavingsTotalSensor(coordinator, entry),
        SmartPriceChargedKwhTotalSensor(coordinator, entry),
    ])

class SmartPriceSensorBase(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_has_entity_name = True
    @property
    def device_info(self): return {"identifiers": {(DOMAIN, self.entry.entry_id)}, "name": "SmartPriceCharge", "manufacturer": "Custom"}

# Status
class SmartPriceStatusSensor(SmartPriceSensorBase):
    _attr_name = "Status"
    _attr_icon = "mdi:robot-outline"
    @property
    def unique_id(self): return f"{self.entry.entry_id}_status"
    @property
    def native_value(self): return self.coordinator.data.get("status", "Init...")

class SmartPriceModeSensor(SmartPriceSensorBase):
    _attr_name = "Modus Empfehlung"
    _attr_icon = "mdi:home-lightning-bolt"
    @property
    def unique_id(self): return f"{self.entry.entry_id}_mode"
    @property
    def native_value(self): return self.coordinator.data.get("mode", "general")

class SmartPriceSessionSensor(SmartPriceSensorBase):
    _attr_name = "Session Geladen"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    @property
    def unique_id(self): return f"{self.entry.entry_id}_session"
    @property
    def native_value(self): return self.coordinator.data.get("session_kwh", 0.0)

# Details
class SmartPriceCurrentPriceSensor(SmartPriceSensorBase):
    _attr_name = "Aktueller Preis"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/kWh"
    @property
    def unique_id(self): return f"{self.entry.entry_id}_current_price"
    @property
    def native_value(self): return self.coordinator.data.get("current_price", 0.0)

class SmartPricePeakPriceSensor(SmartPriceSensorBase):
    _attr_name = "Peak Preis"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/kWh"
    @property
    def unique_id(self): return f"{self.entry.entry_id}_peak_price"
    @property
    def native_value(self): return self.coordinator.data.get("peak_price", 0.0)

class SmartPricePeakTimeSensor(SmartPriceSensorBase):
    _attr_name = "Peak Zeit"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    @property
    def unique_id(self): return f"{self.entry.entry_id}_peak_time"
    @property
    def native_value(self): return self.coordinator.data.get("peak_time")

class SmartPriceNextChargeSensor(SmartPriceSensorBase):
    _attr_name = "Nächste Ladung"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    @property
    def unique_id(self): return f"{self.entry.entry_id}_next_charge"
    @property
    def native_value(self): return self.coordinator.data.get("next_charge_time")

class SmartPriceSlotsInfoSensor(SmartPriceSensorBase):
    _attr_name = "Geplante Slots"
    _attr_icon = "mdi:format-list-bulleted"
    @property
    def unique_id(self): return f"{self.entry.entry_id}_slots_info"
    @property
    def native_value(self): return self.coordinator.data.get("slots_info")

# --- TRACKER (Hier war der Fehler) ---

class SmartPriceCostTotalSensor(SmartPriceSensorBase):
    _attr_name = "Kosten Laden (Gesamt)"
    _attr_device_class = SensorDeviceClass.MONETARY
    # FIX: TOTAL statt TOTAL_INCREASING für Monetary
    _attr_state_class = SensorStateClass.TOTAL 
    _attr_native_unit_of_measurement = CURRENCY_EURO
    @property
    def unique_id(self): return f"{self.entry.entry_id}_track_cost"
    @property
    def native_value(self): return self.coordinator.data.get("track_cost", 0.0)

class SmartPriceSavingsTotalSensor(SmartPriceSensorBase):
    _attr_name = "Ersparnis Laden (Gesamt)"
    _attr_device_class = SensorDeviceClass.MONETARY
    # FIX: TOTAL statt TOTAL_INCREASING
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY_EURO
    @property
    def unique_id(self): return f"{self.entry.entry_id}_track_saved"
    @property
    def native_value(self): return self.coordinator.data.get("track_saved", 0.0)

class SmartPriceDischargeSavingsTotalSensor(SmartPriceSensorBase):
    _attr_name = "Wert Entladung (Gesamt)"
    _attr_device_class = SensorDeviceClass.MONETARY
    # FIX: TOTAL statt TOTAL_INCREASING
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY_EURO
    @property
    def unique_id(self): return f"{self.entry.entry_id}_track_discharge"
    @property
    def native_value(self): return self.coordinator.data.get("track_discharge", 0.0)

class SmartPricePVSavingsTotalSensor(SmartPriceSensorBase):
    _attr_name = "Wert PV Direkt (Gesamt)"
    _attr_device_class = SensorDeviceClass.MONETARY
    # FIX: TOTAL statt TOTAL_INCREASING
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY_EURO
    @property
    def unique_id(self): return f"{self.entry.entry_id}_track_pv"
    @property
    def native_value(self): return self.coordinator.data.get("track_pv", 0.0)

class SmartPriceChargedKwhTotalSensor(SmartPriceSensorBase):
    _attr_name = "Geladen Gesamt (kWh)"
    _attr_device_class = SensorDeviceClass.ENERGY
    # HIER IST TOTAL_INCREASING ERLAUBT (da Energy)
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    @property
    def unique_id(self): return f"{self.entry.entry_id}_track_kwh"
    @property
    def native_value(self): return self.coordinator.data.get("track_kwh", 0.0)