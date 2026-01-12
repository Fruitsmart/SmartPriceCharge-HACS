import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL

from .const import (
    DOMAIN,
    CONF_MIN_SOC,
    CONF_MAX_SOC,
    CONF_CHARGE_POWER,
    CONF_DISCHARGE_POWER,
    DEFAULT_MIN_SOC,
    DEFAULT_MAX_SOC,
    DEFAULT_CHARGE_POWER,
    DEFAULT_DISCHARGE_POWER,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
)

class SmartPriceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Price Charge."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Validierung könnte hier hinzugefügt werden (z.B. Test-Verbindung)
            return self.async_create_entry(title="Smart Price Charge", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartPriceOptionsFlowHandler(config_entry)


class SmartPriceOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Smart Price Charge."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        # WICHTIG: self.config_entry ist in neueren HA-Versionen schreibgeschützt.
        # Wir speichern die Entry-Referenz daher in self._config_entry.
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Wir aktualisieren den Eintrag mit den neuen Daten
            return self.async_create_entry(title="", data=user_input)

        # Werte aus den Optionen laden, Fallback auf Config-Daten oder Defaults
        options = self._config_entry.options
        data = self._config_entry.data

        # Inverter Einstellungen (Host/Port) - Standard aus Config, falls nicht in Optionen überschrieben
        host_default = options.get(CONF_HOST, data.get(CONF_HOST, ""))
        port_default = options.get(CONF_PORT, data.get(CONF_PORT, DEFAULT_PORT))
        scan_default = options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

        # SOC & Power Einstellungen
        min_soc_default = options.get(CONF_MIN_SOC, DEFAULT_MIN_SOC)
        max_soc_default = options.get(CONF_MAX_SOC, DEFAULT_MAX_SOC)
        charge_power_default = options.get(CONF_CHARGE_POWER, DEFAULT_CHARGE_POWER)
        discharge_power_default = options.get(CONF_DISCHARGE_POWER, DEFAULT_DISCHARGE_POWER)

        schema = vol.Schema({
            # Inverter Verbindung
            vol.Required(CONF_HOST, default=host_default): str,
            vol.Required(CONF_PORT, default=port_default): int,
            vol.Optional(CONF_SCAN_INTERVAL, default=scan_default): int,

            # Batterie / SOC Einstellungen
            vol.Optional(CONF_MIN_SOC, default=min_soc_default): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Optional(CONF_MAX_SOC, default=max_soc_default): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            
            # Leistungsgrenzen
            vol.Optional(CONF_CHARGE_POWER, default=charge_power_default): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Optional(CONF_DISCHARGE_POWER, default=discharge_power_default): vol.All(vol.Coerce(int), vol.Range(min=0)),
        })

        return self.async_show_form(step_id="init", data_schema=schema)