"""Config flow für SmartPriceCharge."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import *

_LOGGER = logging.getLogger(__name__)

class SmartPriceChargeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        # FIX: Der Handler wird mit dem config_entry initialisiert
        return SmartPriceOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.context["user_input"] = user_input
            return await self.async_step_sensors()

        data_schema = vol.Schema({
            vol.Required(CONF_TIBBER_TOKEN): str,
            vol.Required(CONF_SOC_SENSOR): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="battery")),
            vol.Required(CONF_INVERTER_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["select", "input_select"])),
            vol.Required(CONF_REFERENCE_PRICE, default=DEFAULT_REF_PRICE): vol.Coerce(float),
            vol.Required(CONF_BATTERY_CAPACITY, default=DEFAULT_CAPACITY): vol.Coerce(float),
            vol.Required(CONF_CHARGER_POWER, default=DEFAULT_CHARGER_POWER): vol.Coerce(float),
        })
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_sensors(self, user_input=None):
        if user_input is not None:
            self.context["user_input"].update(user_input)
            return await self.async_step_forecast()
        data_schema = vol.Schema({
            vol.Required(CONF_PV_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
            vol.Required(CONF_GRID_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
            vol.Required(CONF_BATTERY_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
            vol.Optional(CONF_HOUSE_POWER): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
            vol.Optional(CONF_AVG_CONSUMPTION): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="power")),
        })
        return self.async_show_form(step_id="sensors", data_schema=data_schema)

    async def async_step_forecast(self, user_input=None):
        if user_input is not None:
            data = {**self.context.get("user_input", {}), **user_input}
            return self.async_create_entry(title="SmartPrice Manager", data=data)
        data_schema = vol.Schema({
            # PV Peak Time Sensor
            vol.Optional(CONF_PV_PEAK_TIME): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            
            vol.Optional(CONF_PV_FC_NEXT): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_PV_FC_REM): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_PV_FC_TOMORROW): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_WEATHER_SENSOR): selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
            vol.Optional(CONF_SUN_SENSOR, default="sun.sun"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sun")),
            vol.Optional(CONF_NOTIFY_SERVICE): selector.TextSelector(),
        })
        return self.async_show_form(step_id="forecast", data_schema=data_schema)

class SmartPriceOptionsFlowHandler(config_entries.OptionsFlow):
    """Handhabt die Einstellungen."""

    def __init__(self, config_entry):
        """Initialisiert den OptionsFlow Handler."""
        # FIX: Wir speichern den Eintrag in self._config_entry, da self.config_entry schreibgeschützt ist.
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # FIX: Zugriff auf self._config_entry statt self.config_entry
        opts = self._config_entry.options
        # Fallback auf Data, falls Options noch leer sind
        data = self._config_entry.data
        
        def get_opt(key, default):
            if key in opts: return opts[key]
            if key in data: return data[key]
            return default

        current_inv_entity = get_opt(CONF_INVERTER_MIN_SOC_ENTITY, None)
        current_notify_service = get_opt(CONF_NOTIFY_SERVICE, "")

        schema = vol.Schema({
            # BENACHRICHTIGUNGEN
            vol.Optional(CONF_NOTIFY_ACTIVE, default=get_opt(CONF_NOTIFY_ACTIVE, True)): bool,
            vol.Optional(CONF_NOTIFY_SERVICE, description={"suggested_value": current_notify_service}): selector.TextSelector(),

            # 1. Inverter Logic
            vol.Optional(CONF_INVERTER_MIN_SOC_ENTITY, description={"suggested_value": current_inv_entity}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["number", "input_number", "sensor"])
            ),
            vol.Optional(CONF_INVERTER_MIN_SOC_INVERT, default=get_opt(CONF_INVERTER_MIN_SOC_INVERT, False)): bool,

            # 2. SoC Slider
            vol.Optional(CONF_TARGET_SOC, description={"suggested_value": get_opt(CONF_TARGET_SOC, DEFAULT_TARGET_SOC)}): 
                selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=100, step=5, unit_of_measurement="%")),
            vol.Optional(CONF_MIN_SOC, description={"suggested_value": get_opt(CONF_MIN_SOC, DEFAULT_MIN_SOC)}): 
                selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=100, step=5, unit_of_measurement="%")),

            # 3. Faktoren
            vol.Optional(CONF_BATTERY_EFFICIENCY, description={"suggested_value": get_opt(CONF_BATTERY_EFFICIENCY, DEFAULT_EFFICIENCY)}): vol.Coerce(float),
            vol.Optional(CONF_PV_SAFETY_FACTOR, description={"suggested_value": get_opt(CONF_PV_SAFETY_FACTOR, DEFAULT_PV_SAFETY)}): vol.Coerce(float),
            vol.Optional(CONF_MIN_PROFIT, description={"suggested_value": get_opt(CONF_MIN_PROFIT, DEFAULT_MIN_PROFIT)}): vol.Coerce(float),
            
            # 4. Spread
            vol.Optional(CONF_MIN_SPREAD, description={"suggested_value": get_opt(CONF_MIN_SPREAD, DEFAULT_MIN_SPREAD)}): vol.Coerce(float),
            vol.Optional(CONF_SOC_MED, description={"suggested_value": get_opt(CONF_SOC_MED, DEFAULT_SOC_MED)}): vol.Coerce(float),
            vol.Optional(CONF_SPREAD_MED, description={"suggested_value": get_opt(CONF_SPREAD_MED, DEFAULT_SPREAD_MED)}): vol.Coerce(float),
            vol.Optional(CONF_SOC_HIGH, description={"suggested_value": get_opt(CONF_SOC_HIGH, DEFAULT_SOC_HIGH)}): vol.Coerce(float),
            vol.Optional(CONF_SPREAD_HIGH, description={"suggested_value": get_opt(CONF_SPREAD_HIGH, DEFAULT_SPREAD_HIGH)}): vol.Coerce(float),

            # 5. Sleep Over
            vol.Optional(CONF_SLEEP_SOC, description={"suggested_value": get_opt(CONF_SLEEP_SOC, DEFAULT_SLEEP_SOC)}): vol.Coerce(float),
            vol.Optional(CONF_MORNING_DIFF, description={"suggested_value": get_opt(CONF_MORNING_DIFF, DEFAULT_MORNING_DIFF)}): vol.Coerce(float),
        })
        return self.async_show_form(step_id="init", data_schema=schema)