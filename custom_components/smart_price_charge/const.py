"""Constants for the Smart Price Charge integration."""

DOMAIN = "smart_price_charge"

# --- Basis Konfiguration ---
CONF_TIBBER_TOKEN = "tibber_token"
CONF_SOC_SENSOR = "soc_sensor_entity_id"
CONF_INVERTER_ENTITY = "inverter_entity_id"
CONF_REFERENCE_PRICE = "reference_price"
CONF_BATTERY_CAPACITY = "battery_capacity_kwh"
CONF_CHARGER_POWER = "charger_power_w"

# --- Sensoren Setup ---
CONF_PV_POWER = "pv_power_entity_id"
CONF_GRID_POWER = "grid_power_entity_id"
CONF_BATTERY_POWER = "battery_power_entity_id"
CONF_HOUSE_POWER = "house_power_entity_id"
CONF_AVG_CONSUMPTION = "avg_consumption_entity_id"

# --- Forecast Setup ---
CONF_PV_PEAK_TIME = "pv_peak_time_entity_id"
CONF_PV_FC_NEXT = "pv_forecast_next_hour"
CONF_PV_FC_REM = "pv_forecast_remaining"
CONF_PV_FC_TOMORROW = "pv_forecast_tomorrow"
CONF_WEATHER_SENSOR = "weather_entity_id"
CONF_SUN_SENSOR = "sun_entity_id"

# --- Options / Logik Einstellungen ---
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_ACTIVE = "notify_active"

CONF_INVERTER_MIN_SOC_ENTITY = "inverter_min_soc_entity_id"
CONF_INVERTER_MIN_SOC_INVERT = "inverter_min_soc_invert_logic"

CONF_TARGET_SOC = "target_soc_pct"
CONF_MIN_SOC = "min_soc_pct"

CONF_BATTERY_EFFICIENCY = "battery_efficiency"
CONF_PV_SAFETY_FACTOR = "pv_safety_factor"
CONF_MIN_PROFIT = "min_profit"

CONF_MIN_SPREAD = "min_spread"
CONF_SOC_MED = "soc_med"
CONF_SPREAD_MED = "spread_med"
CONF_SOC_HIGH = "soc_high"
CONF_SPREAD_HIGH = "spread_high"

CONF_SLEEP_SOC = "sleep_soc"
CONF_MORNING_DIFF = "morning_diff"

# --- Default Werte (Defaults) ---
DEFAULT_REF_PRICE = 0.30
DEFAULT_CAPACITY = 10.0
DEFAULT_CHARGER_POWER = 3000.0

DEFAULT_TARGET_SOC = 100
DEFAULT_MIN_SOC = 10
DEFAULT_EFFICIENCY = 0.90
DEFAULT_PV_SAFETY = 1.1
DEFAULT_MIN_PROFIT = 0.02

DEFAULT_MIN_SPREAD = 0.05
DEFAULT_SOC_MED = 50
DEFAULT_SPREAD_MED = 0.10
DEFAULT_SOC_HIGH = 80
DEFAULT_SPREAD_HIGH = 0.15

DEFAULT_SLEEP_SOC = 15
DEFAULT_MORNING_DIFF = 0.05