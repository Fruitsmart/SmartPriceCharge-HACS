"""Config flow für SmartPriceCharge."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import *

_LOGGER = logging.getLogger(__name__)

# --- SAFETY FALLBACKS ---
# Falls HACS/HA alte const.py cachen oder Imports fehlschlagen.
if 'DEFAULT_MODE_NORMAL' not in locals():
    DEFAULT_MODE_NORMAL = "Normal"
if 'DEFAULT_MODE_FORCE' not in locals():
    DEFAULT_MODE_FORCE = "ForceCharge"
# ------------------------

class SmartPriceChargeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartPriceOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Schritt 1: Initiale Einrichtung."""
        if user_input is not None:
            self.context["user_input"] = user_input
            return await self.async_step_sensors()

        data_schema = vol.Schema({
            # --- 1. GRUNDLAGEN ---
            vol.Required(CONF_TIBBER_TOKEN): str,
            vol.Required(CONF_SOC_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="battery")
            ),
            
            # --- 2. INVERTER MODUS ---
            vol.Required(CONF_INVERTER_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["select", "input_select"])
            ),
            # FIX: Jetzt nutzen wir sicher die Konstanten
            vol.Required(CONF_MODE_OPTION_NORMAL, default=DEFAULT_MODE_NORMAL): str,
            vol.Required(CONF_MODE_OPTION_FORCE_CHARGE, default=DEFAULT_MODE_FORCE): str,
            
            # --- 3. INVERTER LIMITS ---
            vol.Optional(CONF_INVERTER_MIN_SOC_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["number", "input_number", "sensor"])
            ),
            vol.Optional(CONF_INVERTER_MIN_SOC_INVERT, default=False): bool,

            # --- 4. SPEICHER DATEN ---
            vol.Required(CONF_REFERENCE_PRICE, default=DEFAULT_REF_PRICE): vol.Coerce(float),
            vol.Required(CONF_BATTERY_CAPACITY, default=DEFAULT_CAPACITY): vol.Coerce(float),
            vol.Required(CONF_CHARGER_POWER, default=DEFAULT_CHARGER_POWER): vol.Coerce(float),
        })
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_sensors(self, user_input=None):
        """Schritt 2: Sensoren."""
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
        """Schritt 3: Forecast & Abschluss."""
        if user_input is not None:
            data = {**self.context.get("user_input", {}), **user_input}
            return self.async_create_entry(title="SmartPrice Manager", data=data)
        data_schema = vol.Schema({
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
        # FIX für 'AttributeError: property config_entry has no setter'
        # In neuen HA Versionen darf man self.config_entry nicht direkt setzen.
        # Man muss die interne Variable self._config_entry (mit Unterstrich) nutzen.
        self._config_entry = config_entry
        # Super init aufrufen (sicherer als der alte try/except Block)
        super().__init__()

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Da wir self._config_entry gesetzt haben, funktioniert der Zugriff
        # auf self.config_entry (Property) jetzt korrekt.
        opts = self.config_entry.options
        data = self.config_entry.data
        
        def get_opt(key, default):
            if key in opts: return opts[key]
            if key in data: return data[key]
            return default

        current_inv_entity = get_opt(CONF_INVERTER_MIN_SOC_ENTITY, None)
        current_notify_service = get_opt(CONF_NOTIFY_SERVICE, "")
        
        curr_mode_normal = get_opt(CONF_MODE_OPTION_NORMAL, DEFAULT_MODE_NORMAL)
        curr_mode_charge = get_opt(CONF_MODE_OPTION_FORCE_CHARGE, DEFAULT_MODE_FORCE)

        schema = vol.Schema({
            # BENACHRICHTIGUNGEN
            vol.Optional(CONF_NOTIFY_ACTIVE, default=get_opt(CONF_NOTIFY_ACTIVE, True)): bool,
            vol.Optional(CONF_NOTIFY_SERVICE, description={"suggested_value": current_notify_service}): selector.TextSelector(),

            # 1. Inverter Logic
            vol.Optional(CONF_MODE_OPTION_NORMAL, default=curr_mode_normal): str,
            vol.Optional(CONF_MODE_OPTION_FORCE_CHARGE, default=curr_mode_charge): str,

            # 2. Inverter SoC Limit
            vol.Optional(CONF_INVERTER_MIN_SOC_ENTITY, description={"suggested_value": current_inv_entity}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["number", "input_number", "sensor"])
            ),
            vol.Optional(CONF_INVERTER_MIN_SOC_INVERT, default=get_opt(CONF_INVERTER_MIN_SOC_INVERT, False)): bool,

            # 3. SoC Slider
            vol.Optional(CONF_TARGET_SOC, description={"suggested_value": get_opt(CONF_TARGET_SOC, DEFAULT_TARGET_SOC)}): 
                selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=100, step=5, unit_of_measurement="%")),
            vol.Optional(CONF_MIN_SOC, description={"suggested_value": get_opt(CONF_MIN_SOC, DEFAULT_MIN_SOC)}): 
                selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=100, step=5, unit_of_measurement="%")),

            # 4. Faktoren
            vol.Optional(CONF_BATTERY_EFFICIENCY, description={"suggested_value": get_opt(CONF_BATTERY_EFFICIENCY, DEFAULT_EFFICIENCY)}): vol.Coerce(float),
            vol.Optional(CONF_PV_SAFETY_FACTOR, description={"suggested_value": get_opt(CONF_PV_SAFETY_FACTOR, DEFAULT_PV_SAFETY)}): vol.Coerce(float),
            vol.Optional(CONF_MIN_PROFIT, description={"suggested_value": get_opt(CONF_MIN_PROFIT, DEFAULT_MIN_PROFIT)}): vol.Coerce(float),
            
            # 5. Spread
            vol.Optional(CONF_MIN_SPREAD, description={"suggested_value": get_opt(CONF_MIN_SPREAD, DEFAULT_MIN_SPREAD)}): vol.Coerce(float),
            vol.Optional(CONF_SOC_MED, description={"suggested_value": get_opt(CONF_SOC_MED, DEFAULT_SOC_MED)}): vol.Coerce(float),
            vol.Optional(CONF_SPREAD_MED, description={"suggested_value": get_opt(CONF_SPREAD_MED, DEFAULT_SPREAD_MED)}): vol.Coerce(float),
            vol.Optional(CONF_SOC_HIGH, description={"suggested_value": get_opt(CONF_SOC_HIGH, DEFAULT_SOC_HIGH)}): vol.Coerce(float),
            vol.Optional(CONF_SPREAD_HIGH, description={"suggested_value": get_opt(CONF_SPREAD_HIGH, DEFAULT_SPREAD_HIGH)}): vol.Coerce(float),

            # 6. Sleep Over
            vol.Optional(CONF_SLEEP_SOC, description={"suggested_value": get_opt(CONF_SLEEP_SOC, DEFAULT_SLEEP_SOC)}): vol.Coerce(float),
            vol.Optional(CONF_MORNING_DIFF, description={"suggested_value": get_opt(CONF_MORNING_DIFF, DEFAULT_MORNING_DIFF)}): vol.Coerce(float),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
