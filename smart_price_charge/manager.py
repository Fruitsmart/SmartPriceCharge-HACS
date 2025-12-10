"""Logik Manager für SmartPriceCharge (Full Logic + Panic + Dip + Exact Slots + PV Aware)."""
import logging
import aiohttp
import math
from datetime import timedelta, datetime
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.util.dt as dt_util
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from .const import *

_LOGGER = logging.getLogger(__name__)

# Wetter Faktoren
WEATHER_PV_FACTOR = {
    'sunny': 1.0, 'clear-night': 0.0, 'partlycloudy': 0.8, 'cloudy': 0.5,
    'fog': 0.3, 'rainy': 0.1, 'pouring': 0.05, 'snowy': 0.4,
    'lightning': 0.1, 'hail': 0.1, 'windy': 0.5, 'exceptional': 0.0
}

class SmartPriceChargeManager(DataUpdateCoordinator):
    """Hauptlogik."""

    def __init__(self, hass, entry):
        self.entry = entry
        self.config = entry.data
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=60))

        self.is_active = True
        self.tibber_token = self.config.get(CONF_TIBBER_TOKEN)
        self.notify_service_static = self.config.get(CONF_NOTIFY_SERVICE)
        self.ref_price = self.config.get(CONF_REFERENCE_PRICE, 0.35)
        
        self.prices_today = []
        self.prices_tomorrow = []
        self.current_api_price = 0.0
        
        # Tracker
        self.tracker_cost_total = 0.0
        self.tracker_savings_total = 0.0
        self.tracker_discharge_savings = 0.0
        self.tracker_pv_savings = 0.0
        self.tracker_charged_kwh = 0.0
        
        # Output States
        self.status_message = "Init..."
        self.recommendation_mode = "general"
        self.charging_session_net_charged_kwh = 0.0
        self.peak_price = 0.0
        self.peak_time = None
        self.next_charge_time = None
        self.slots_info = "Keine Slots"

        self.charging_session_active = False
        self.last_mode_command_time = None
        self.last_limit_command_time = None
        self.last_sleep_over_notified_date = None

    async def _fetch_tibber_data(self):
        if not self.tibber_token: return
        query = """
        { viewer { homes { currentSubscription { priceInfo {
          current { total }
          today { total startsAt }
          tomorrow { total startsAt }
        } } } } }
        """
        url = "https://api.tibber.com/v1-beta/gql"
        headers = {"Authorization": f"Bearer {self.tibber_token}", "Content-Type": "application/json"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"query": query}, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pi = data['data']['viewer']['homes'][0]['currentSubscription']['priceInfo']
                        self.current_api_price = pi['current']['total']
                        self.prices_today = pi['today']
                        self.prices_tomorrow = pi['tomorrow']
        except Exception as e:
            _LOGGER.error(f"Tibber API Error: {e}")

    async def _send_push(self, title, message):
        opts = self.entry.options
        is_active = opts.get(CONF_NOTIFY_ACTIVE, True)
        if not is_active: return
        service = opts.get(CONF_NOTIFY_SERVICE)
        if not service: service = self.notify_service_static
        if not service: return
        domain = "notify"
        service_name = service
        if "." in service: domain, service_name = service.split(".", 1)
        try: await self.hass.services.async_call(domain, service_name, {"title": title, "message": message})
        except: pass

    async def _async_update_data(self):
        if not self.prices_today or dt_util.now().minute % 15 == 0: await self._fetch_tibber_data()
        if not self.is_active: return self._get_data_dict("Deaktiviert")
        try:
            await self.run_logic()
            return self._get_data_dict(self.status_message)
        except Exception as e:
            _LOGGER.error(f"Logic Error: {e}")
            return self._get_data_dict(f"Error: {e}")

    def _get_data_dict(self, status):
        return {
            "status": status,
            "mode": self.recommendation_mode,
            "session_kwh": self.charging_session_net_charged_kwh,
            "current_price": self.current_api_price,
            "peak_price": self.peak_price,
            "peak_time": self.peak_time,
            "next_charge_time": self.next_charge_time,
            "slots_info": self.slots_info,
            "track_cost": self.tracker_cost_total,
            "track_saved": self.tracker_savings_total,
            "track_discharge": self.tracker_discharge_savings,
            "track_pv": self.tracker_pv_savings,
            "track_kwh": self.tracker_charged_kwh
        }

    def _get_float(self, entity_id, default=0.0):
        if not entity_id: return default
        state = self.hass.states.get(entity_id)
        if state and state.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
            try: return float(state.state)
            except: pass
        return default

    async def _set_inverter_mode(self, target_mode):
        self.recommendation_mode = target_mode
        entity = self.config.get(CONF_INVERTER_ENTITY)
        if not entity: return
        now = dt_util.now()
        should_send = True
        if self.last_mode_command_time:
             if (now - self.last_mode_command_time).total_seconds() < 900: 
                 cur_state = self.hass.states.get(entity)
                 if cur_state and cur_state.state == target_mode: should_send = False
        if should_send:
            domain = "input_select" if "input_select" in entity else "select"
            try:
                await self.hass.services.async_call(domain, "select_option", {"entity_id": entity, "option": target_mode})
                self.last_mode_command_time = now
            except: pass

    async def _set_inverter_limit(self, target_min_soc):
        opts = self.entry.options
        entity = opts.get(CONF_INVERTER_MIN_SOC_ENTITY)
        invert_logic = opts.get(CONF_INVERTER_MIN_SOC_INVERT, False)
        if not entity: return 
        target_value = 100.0 - target_min_soc if invert_logic else target_min_soc
        target_value = max(0, min(100, int(target_value)))
        current_val = self._get_float(entity, -1)
        if abs(current_val - target_value) > 1:
            try: await self.hass.services.async_call("number", "set_value", {"entity_id": entity, "value": target_value})
            except: pass

    async def run_logic(self):
        # 1. LIVE DATEN
        batt_cap = self.config.get(CONF_BATTERY_CAPACITY)
        charge_power = self.config.get(CONF_CHARGER_POWER, 3.0) 
        
        cur_soc = self._get_float(self.config.get(CONF_SOC_SENSOR))
        cur_grid = self._get_float(self.config.get(CONF_GRID_POWER))
        cur_house = self._get_float(self.config.get(CONF_HOUSE_POWER), default=0.0)
        cur_pv = self._get_float(self.config.get(CONF_PV_POWER), default=0.0)
        avg_house = self._get_float(self.config.get(CONF_AVG_CONSUMPTION), default=500.0)
        
        # 2. OPTIONEN
        opts = self.entry.options
        target_soc = opts.get(CONF_TARGET_SOC, DEFAULT_TARGET_SOC)
        default_min_soc = opts.get(CONF_MIN_SOC, DEFAULT_MIN_SOC)
        
        inv_limit_entity = opts.get(CONF_INVERTER_MIN_SOC_ENTITY)
        inv_invert_logic = opts.get(CONF_INVERTER_MIN_SOC_INVERT, False)
        user_min_soc = default_min_soc 
        if inv_limit_entity:
            live_limit = self._get_float(inv_limit_entity, default=None)
            if live_limit is not None:
                if inv_invert_logic: user_min_soc = 100.0 - live_limit
                else: user_min_soc = live_limit
                user_min_soc = max(0.0, user_min_soc)

        # 3. FORECAST & WETTER & SONNE
        fc_rem = self._get_float(self.config.get(CONF_PV_FC_REM), default=0.0)
        fc_next = self._get_float(self.config.get(CONF_PV_FC_NEXT), default=0.0)
        
        sun_id = self.config.get(CONF_SUN_SENSOR)
        sun_elevation = 0
        if sun_id:
            try: sun_elevation = float(self.hass.states.get(sun_id).attributes.get('elevation', 0))
            except: pass
        
        weather_id = self.config.get(CONF_WEATHER_SENSOR)
        weather_factor = 0.5
        if weather_id:
            w_state = self.hass.states.get(weather_id)
            if w_state and w_state.state in WEATHER_PV_FACTOR:
                weather_factor = WEATHER_PV_FACTOR[w_state.state]

        # NEU: PV PEAK ZEIT PRÜFEN
        pv_peak_id = self.config.get(CONF_PV_PEAK_TIME)
        approaching_peak = False
        now = dt_util.now()
        
        if pv_peak_id:
            pv_peak_state = self.hass.states.get(pv_peak_id)
            if pv_peak_state and pv_peak_state.state not in [STATE_UNAVAILABLE, STATE_UNKNOWN]:
                try:
                    pv_peak_dt = datetime.fromisoformat(pv_peak_state.state)
                    # Sicherstellen Zeitzone passt
                    if pv_peak_dt.tzinfo is None:
                        pv_peak_dt = pv_peak_dt.replace(tzinfo=now.tzinfo)
                    
                    diff_min = (pv_peak_dt - now).total_seconds() / 60
                    # Peak kommt in 30 Min bis 90 Min?
                    if -30 < diff_min < 90:
                        approaching_peak = True
                except: pass

        # SONNEN LOGIK (is_sun_shining)
        is_daylight = sun_elevation > 0
        forecast_strong = fc_next > 0.1
        pv_active = cur_pv > 50
        
        is_sun_shining = False
        if pv_active: is_sun_shining = True
        elif is_daylight and weather_factor >= 0.4 and forecast_strong: is_sun_shining = True
        elif approaching_peak: is_sun_shining = True

        # 4. PREISE
        prices_all = []
        for p in self.prices_today + self.prices_tomorrow:
            dt = datetime.fromisoformat(p['startsAt']).astimezone(now.tzinfo)
            prices_all.append({'time': dt, 'price': p['total']})
        future_prices = [p for p in prices_all if p['time'] >= now.replace(minute=0, second=0, microsecond=0)]
        
        if not future_prices:
            self.status_message = "Keine Preise"
            return
            
        curr_p = self.current_api_price
        max_item = max(future_prices, key=lambda x: x['price'])
        self.peak_price = max_item['price']
        self.peak_time = max_item['time']

        # TRACKING
        if cur_pv > 0 and cur_house > 0: self.tracker_pv_savings += ((min(cur_pv, cur_house) / 1000) / 60) * curr_p
        if self.charging_session_active and cur_grid < -50:
             kwh_grid = (abs(cur_grid) / 1000) / 60
             self.charging_session_net_charged_kwh += kwh_grid
             self.tracker_charged_kwh += kwh_grid
             self.tracker_cost_total += kwh_grid * curr_p
             self.tracker_savings_total += kwh_grid * (self.ref_price - curr_p)
        cur_bat_pwr = self._get_float(self.config.get(CONF_BATTERY_POWER))
        if cur_bat_pwr > 50: self.tracker_discharge_savings += ((cur_bat_pwr / 1000) / 60) * curr_p

        # 5. LOGIK ENTSCHEIDUNG
        new_mode = "general"
        msg = "Standardbetrieb"
        panic_mode = False
        
        if self.peak_time:
            hours_to_peak = (self.peak_time - now).total_seconds() / 3600
            if 0 < hours_to_peak < 1.5 and cur_soc < (user_min_soc + 5.0):
                panic_mode = True
        
        base_spread = opts.get(CONF_MIN_SPREAD, DEFAULT_MIN_SPREAD)
        soc_med = opts.get(CONF_SOC_MED, DEFAULT_SOC_MED)
        spread_med = opts.get(CONF_SPREAD_MED, DEFAULT_SPREAD_MED)
        soc_high = opts.get(CONF_SOC_HIGH, DEFAULT_SOC_HIGH)
        spread_high = opts.get(CONF_SPREAD_HIGH, DEFAULT_SPREAD_HIGH)
        
        eff_spread = base_spread
        if cur_soc > soc_high: eff_spread = max(eff_spread, spread_high)
        elif cur_soc > soc_med: eff_spread = max(eff_spread, spread_med)
        
        price_spread = self.peak_price - curr_p
        should_hold = (price_spread >= eff_spread)
        
        target_effective_min_soc = user_min_soc
        sleep_over_active = False
        morning_diff = opts.get(CONF_MORNING_DIFF, DEFAULT_MORNING_DIFF)
        sleep_soc = opts.get(CONF_SLEEP_SOC, DEFAULT_SLEEP_SOC)
        
        if now.hour >= 18 and self.prices_tomorrow:
            morning_prices = [p for p in prices_all if p['time'].date() == (now.date() + timedelta(days=1)) and 5 <= p['time'].hour <= 9]
            if morning_prices:
                morning_peak = max(morning_prices, key=lambda x: x['price'])['price']
                if (morning_peak - curr_p) > morning_diff:
                    target_effective_min_soc = sleep_soc
                    sleep_over_active = True
                    today_str = now.strftime('%Y-%m-%d')
                    if self.last_sleep_over_notified_date != today_str:
                        await self._send_push("Sleep-Over 🌙", f"Reserviere {target_effective_min_soc}% Akku.")
                        self.last_sleep_over_notified_date = today_str

        await self._set_inverter_limit(target_effective_min_soc)
        effective_min_soc = target_effective_min_soc

        # SLOTS
        deadline = self.peak_time if (self.peak_price > 0.30 and self.peak_time > now) else datetime.combine(now.date(), time(23, 59)).astimezone(now.tzinfo)
        pool = sorted([x for x in future_prices if x['time'] < deadline], key=lambda x: x['price'])
        
        first_slot_dt = pool[0]['time'] if pool else now
        time_until_slot = (first_slot_dt - now).total_seconds() / 3600
        calc_load = avg_house
        if time_until_slot <= 1.0 and cur_house > 0: calc_load = (cur_house * 0.7) + (avg_house * 0.3)
        calc_load = max(200.0, min(1500.0, calc_load))
        consumption_until = (calc_load / 1000) * max(0, time_until_slot)
        soc_need_kwh = max(0.0, (target_soc - cur_soc) / 100 * batt_cap)
        pv_deduction = fc_rem * opts.get(CONF_PV_SAFETY_FACTOR, DEFAULT_PV_SAFETY)
        needed_kwh = (consumption_until + soc_need_kwh) - pv_deduction
        needed_kwh = max(0.0, min(needed_kwh, batt_cap))
        
        slots_needed_count = 0
        if charge_power > 0 and needed_kwh > 0:
            slots_needed_count = min(math.ceil(needed_kwh / charge_power * 4), 16)
        
        cheap_slots = []
        if slots_needed_count > 0 and len(pool) >= slots_needed_count:
            cheap_slots = sorted(pool[:slots_needed_count], key=lambda x: x['time'])
            start_str = cheap_slots[0]['time'].strftime('%H:%M')
            end_dt = cheap_slots[-1]['time'] + timedelta(minutes=15)
            end_str = end_dt.strftime('%H:%M')
            avg_p = sum(x['price'] for x in cheap_slots) / len(cheap_slots)
            self.slots_info = f"{len(cheap_slots)}x 15min ({start_str}...{end_str}) Ø {avg_p:.3f} €"
            self.next_charge_time = cheap_slots[0]['time']
        else:
            self.slots_info = "Keine Slots nötig"
            self.next_charge_time = None

        is_cheap_now = any(t['time'].hour == now.hour and (t['time'].minute // 15) == (now.minute // 15) for t in cheap_slots)
        
        # --- ZIEL LOGIK ---
        
        # 1. PANIC
        if panic_mode:
            new_mode = "eco_charge"
            msg = f"PANIK! SoC < {user_min_soc+5}%. Peak bald."
            if not self.charging_session_active:
                 self.charging_session_active = True
                 self.charging_session_net_charged_kwh = 0.0

        # 2. ENTLADEN (Aber WARTEN bei Sonne/Hold!)
        elif (curr_p > 0.30 or (price_spread < eff_spread and not is_cheap_now)):
            # WICHTIG: Wenn Sonne scheint ODER Hold aktiv -> NICHT entladen!
            if is_sun_shining:
                new_mode = "general"
                msg = "Warten (PV/Peak erwartet)."
            elif should_hold and curr_p > 0.30: # Hold nur relevant wenn Preis hoch ist
                new_mode = "general"
                msg = f"Warten (Peak erwartet: {self.peak_price:.3f}€)"
            else:
                # Entladen erlaubt
                if cur_soc > effective_min_soc:
                    new_mode = "general"
                    msg = f"Entladen (Preis: {curr_p:.3f}€)"
                    if price_spread < eff_spread: msg = "Entladen (Spread zu klein)."
                else:
                    new_mode = "general"
                    msg = f"Reserve erreicht ({effective_min_soc}%)."

        # 3. LADEN
        elif is_cheap_now and cur_soc < target_soc and needed_kwh > 0.1:
            new_mode = "eco_charge"
            msg = f"Laden bis {target_soc}% ({curr_p:.3f}€)"
            if not self.charging_session_active:
                self.charging_session_active = True
                self.charging_session_net_charged_kwh = 0.0
                await self._send_push("Smart Charge Start 🔋", f"Preis: {curr_p:.3f}€")

        # 4. WARTEN
        else:
            new_mode = "general"
            msg = "Warten (Standardbetrieb)."
            if sleep_over_active: msg = f"Warten (Sleep-Over {effective_min_soc}%)"
            elif should_hold: msg = "Warten (Spread/Hold)"
            elif is_sun_shining: msg = "Warten (PV/Peak erwartet)"
            
            if self.charging_session_active:
                self.charging_session_active = False
                if self.charging_session_net_charged_kwh > 0.5:
                     await self._send_push("Smart Charge Ende ✅", f"Geladen: {self.charging_session_net_charged_kwh:.2f} kWh")

        self.status_message = msg
        await self._set_inverter_mode(new_mode)