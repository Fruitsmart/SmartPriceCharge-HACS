"""Konstanten für SmartPriceCharge."""
DOMAIN = "smart_price_charge"

# Konfigurations-Keys
CONF_TIBBER_TOKEN = "tibber_api_token"
CONF_SOC_SENSOR = "current_soc_sensor_id"
CONF_INVERTER_ENTITY = "inverter_mode_entity_id"
CONF_MODE_OPTION_NORMAL = "mode_option_normal"
CONF_MODE_OPTION_FORCE_CHARGE = "mode_option_force_charge"
CONF_INVERTER_MIN_SOC_ENTITY = "inverter_min_soc_entity_id"
CONF_INVERTER_MIN_SOC_INVERT = "inverter_min_soc_invert_logic"
CONF_REFERENCE_PRICE = "reference_price_eur"
CONF_BATTERY_CAPACITY = "battery_capacity_kwh"
CONF_CHARGER_POWER = "charger_power_kw"

# Sensoren & Forecast
CONF_PV_POWER = "current_pv_power_sensor_id"
CONF_GRID_POWER = "grid_power_import_export_sensor_id"
CONF_BATTERY_POWER = "battery_power_sensor_id"
CONF_HOUSE_POWER = "current_house_consumption_id"
CONF_AVG_CONSUMPTION = "avg_consumption_sensor_id"
CONF_PV_FC_NEXT = "pv_forecast_sensor_id"
CONF_PV_FC_REM = "pv_forecast_today_remaining_sensor_id"
CONF_PV_FC_TOMORROW = "pv_forecast_tomorrow_sensor_id"
CONF_PV_PEAK_TIME = "pv_peak_time_sensor_id"
CONF_SUN_SENSOR = "sun_sensor_id"
CONF_WEATHER_SENSOR = "weather_sensor_id"

# AI & Settings
CONF_NOTIFY_SERVICE = "notification_service"
CONF_NOTIFY_ACTIVE = "notification_active"
CONF_AI_ACTIVE = "ai_active"
CONF_GEMINI_API_KEY = "gemini_api_key"
CONF_AI_OUTPUT_ENTITY = "ai_advice_text_id"
CONF_INVERTER_MAX_SOC_ENTITY = "inverter_max_soc_entity_id"
CONF_BATTERY_EFFICIENCY = "battery_efficiency_factor"
CONF_PV_SAFETY_FACTOR = "pv_forecast_safety_factor"
CONF_MIN_PROFIT = "min_cycle_profit_eur"
CONF_MIN_SPREAD = "min_price_spread_eur"
CONF_SOC_MED = "soc_threshold_medium"
CONF_SPREAD_MED = "spread_medium_soc_eur"
CONF_SOC_HIGH = "soc_threshold_high"
CONF_SPREAD_HIGH = "spread_high_soc_eur"
CONF_SLEEP_SOC = "sleep_over_soc"
CONF_MORNING_DIFF = "morning_min_diff"
CONF_TARGET_SOC = "target_soc_pct"
CONF_MIN_SOC = "min_soc_pct"

# Standardwerte (Fix für den Manager-Error)
DEFAULT_TARGET_SOC = 100.0
DEFAULT_MIN_SOC = 10.0
DEFAULT_MIN_SPREAD = 0.04
DEFAULT_SOC_MED = 75.0
DEFAULT_SPREAD_MED = 0.15
DEFAULT_SOC_HIGH = 90.0
DEFAULT_SPREAD_HIGH = 0.25
DEFAULT_SLEEP_SOC = 30.0
DEFAULT_MORNING_DIFF = 0.10
DEFAULT_EFFICIENCY = 0.90
DEFAULT_PV_SAFETY = 0.50
DEFAULT_MIN_PROFIT = 0.02