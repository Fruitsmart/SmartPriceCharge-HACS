"""SmartPriceCharge Init."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .manager import SmartPriceChargeManager

PLATFORMS = ["sensor", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setze die Integration auf."""
    hass.data.setdefault(DOMAIN, {})
    
    manager = SmartPriceChargeManager(hass, entry)
    await manager.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = manager
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Listener für Einstellungs-Änderungen
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlade die Integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Lädt die Integration neu, wenn Optionen geändert wurden."""
    await hass.config_entries.async_reload(entry.entry_id)