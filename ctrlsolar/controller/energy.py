from datetime import datetime, timedelta
from ctrlsolar.abstracts import Panel, Weather, Controller, DCCoupledBattery, Consumer
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class EnergyForecast:
    name: str = "EnergyForecast"

    def __init__(
        self,
        weather: Weather,
        panels: list[Panel],
        max_age: timedelta = timedelta(hours=1),
    ):
        self.weather = weather
        self.panels = panels
        self.max_age = max_age
        self._weather: pd.DataFrame | None = None
        self._weather_age = None

    def _update_forecast(self) -> None:
        if self._weather is None:
            self._weather = self.weather.get()
            self._weather_age = datetime.now()
        else:
            if self._weather_age is not None:
                if datetime.now() - self._weather_age > self.max_age:
                    self._weather = self.weather.get()
                    self._weather_age = datetime.now()

        return

    def daily_production_estimate(self) -> float:
        self._update_forecast()
        p_dcs = 0.0
        if self._weather is not None:
            p_dcs = sum([float(x.predicted_production_by_hour(forecast=self._weather).values.sum()) for x in self.panels])
        
        return p_dcs

    def hourly_production_estimate(self) -> list[float,]:
        self._update_forecast()
        p_dcs = 24*[0.]
        if self._weather is not None:
            p_dcs = np.sum(np.column_stack([x.predicted_production_by_hour(forecast=self._weather).values for x in self.panels]), axis=-1, keepdims=False).tolist()
        
        return p_dcs

    def remaining_energy_production_today(self, remaining_hours: int) -> float:
        hour = datetime.now().hour                  
        energy = sum(self.hourly_production_estimate()[hour:hour+remaining_hours])
        return energy

    def remaining_production_hours_today(self, cutoff_energy_kWh: float) -> int:
        hour = datetime.now().hour  
        energy = self.hourly_production_estimate()[hour:]         
        index = [x < cutoff_energy_kWh for x in energy].index(True)
        return index
    

class EnergyController(Controller):
    def __init__(self, battery: DCCoupledBattery, forecast: EnergyForecast, p_min: float, p_max: float, power: Consumer):
        self._power_setter = power
        self._battery = battery
        self._forecast = forecast
        self._p_min_limit = p_min
        self._p_max_limit = p_max
        
        return 
    
    def evaluate_day_schedule(self) -> None:
        energy = self._forecast.hourly_production_estimate()
        prod_start = [x > self._p_min_limit for x in energy].index(True)
        prod_end = prod_start + [x < self._p_min_limit for x in energy[prod_start:]].index(True)

        self._production_hours = [*range(prod_start, prod_end)]
        self._battery_hours = [h for h in range(24) if h not in self._production_hours]
        return 
    
    def evaluate_production_power_target(self) -> float:
        missing_Wh = self._battery.energy_missing
        
        if missing_Wh is None: 
            logger.warning(f"Missing information about battery charge state! Assuming battery empty.")
            missing_Wh = self._battery.capacity

        prod_remaining_h = self._forecast.remaining_production_hours_today(cutoff_energy_kWh=self._p_min_limit * 1)  # 1h
        prod_remaining_Wh = self._forecast.remaining_energy_production_today(remaining_hours=prod_remaining_h)

        target_W = min(
            (prod_remaining_Wh - missing_Wh) / prod_remaining_h,
            self._p_max_limit
        )
        
        return target_W
    
    def evaluate_battery_power_target(self) -> float:
        charge = self._battery.energy_charged
        if charge is None:
            logger.warning(f"Missing information about battery charge state! Assuming battery full.")
            charge = self._battery.capacity

        target_W = charge / len(self._battery_hours)
        return target_W


    def update(self):
        hour = datetime.now().hour

        if hour in self._battery_hours:
            target_W = self.evaluate_battery_power_target()
            logger.info(f"Hour {hour}/24, which is battery mode. Power-target is evaluated to {target_W} W.")
            
        if hour in self._production_hours:
            target_W = self.evaluate_production_power_target()
            logger.info(f"Hour {hour}/24, which is production mode. Power-target is evaluated to {target_W} W.")

        else:
            logger.warning(f"Something went terribly wrong. Setting fallback power of 200W.")
            target_W = 200

        self._power_setter.set(target_W)
        return 