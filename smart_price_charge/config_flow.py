"""Konfigurations-Fluss für SmartPriceCharge."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import *

_LOGGER = logging.getLogger(__name__)

class SmartPriceChargeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Setup Flow mit 3 Schritten."""
    VERSION = 1

    def __init__(self):
        """Initialisiert den Datenspeicher."""
        self._data = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Erstellt das Options-Menü ohne Übergabe-Fehler."""
        return SmartPriceOptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        """Schritt 1/3: Verbindung."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TIBBER_TOKEN): str,
                vol.Required(CONF_SOC_SENSOR): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="battery")),
                vol.Required(CONF_INVERTER_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["select", "input_select"])),
                vol.Required(CONF_MODE_OPTION_NORMAL, default="Normal"): str,
                vol.Required(CONF_MODE_OPTION_FORCE_CHARGE, default="ForceCharge"): str,
                vol.Optional(CONF_INVERTER_MIN_SOC_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["number", "input_number", "sensor"])),
                vol.Optional(CONF_INVERTER_MIN_SOC_INVERT, default=False): bool,
                vol.Required(CONF_REFERENCE_PRICE, default=0.35): vol.Coerce(float),
                vol.Required(CONF_BATTERY_CAPACITY, default=5.0): vol.Coerce(float),
                vol.Required(CONF_CHARGER_POWER, default=3.0): vol.Coerce(float),
            })
        )

    async def async_step_sensors(self, user_input=None):
        """Schritt 2/3: Leistungssensoren."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_forecast()

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema({
                vol.Required(CONF_PV_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
                vol.Required(CONF_GRID_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
                vol.Required(CONF_BATTERY_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
                vol.Optional(CONF_HOUSE_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
                vol.Optional(CONF_AVG_CONSUMPTION): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
            })
        )

    async def async_step_forecast(self, user_input=None):
        """Schritt 3/3: Forecast & Abschluss."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="SmartPrice Manager", data=self._data)

        return self.async_show_form(
            step_id="forecast",
            data_schema=vol.Schema({
                vol.Optional(CONF_PV_FC_NEXT): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(CONF_PV_PEAK_TIME): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(CONF_WEATHER_SENSOR): selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
                vol.Optional(CONF_SUN_SENSOR, default="sun.sun"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sun")),
                vol.Optional(CONF_NOTIFY_SERVICE): selector.TextSelector(),
            })
        )

class SmartPriceOptionsFlowHandler(config_entries.OptionsFlow):
    """Menü für spätere Änderungen (Konfigurieren-Button)."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Holen der aktuellen Werte
        opts = self.config_entry.options
        data = self.config_entry.data
        def get_o(k, d): return opts.get(k, data.get(k, d))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_MODE_OPTION_NORMAL, default=get_o(CONF_MODE_OPTION_NORMAL, "Normal")): str,
                vol.Optional(CONF_MODE_OPTION_FORCE_CHARGE, default=get_o(CONF_MODE_OPTION_FORCE_CHARGE, "ForceCharge")): str,
                vol.Optional(CONF_AI_ACTIVE, default=get_o(CONF_AI_ACTIVE, False)): bool,
                vol.Optional(CONF_GEMINI_API_KEY, default=get_o(CONF_GEMINI_API_KEY, "")): str,
                vol.Optional(CONF_TARGET_SOC, default=get_o(CONF_TARGET_SOC, 100.0)): vol.Coerce(float),
                vol.Optional(CONF_MIN_SOC, default=get_o(CONF_MIN_SOC, 10.0)): vol.Coerce(float),
            })
        )