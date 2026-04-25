from datetime import datetime
from ctrlsolar.panels.abstract import Weather, Panel
from ctrlsolar.battery.abstract import DCCoupledBattery
from ctrlsolar.controller.abstract import Controller
import logging

logger = logging.getLogger(__name__)

class EnergyForecast:
    name: str = "EnergyForecast"

    def __init__(
        self,
        weather: Weather,
        panels: Panel,
    ):
        self._weather = weather
        self._panels = panels

    def daily_production_estimate(self) -> float:
        p_dcs = sum(self.hourly_production_estimate())
        
        return p_dcs

    def hourly_production_estimate(self) -> list[float,]:
        return self._panels.predicted_production_by_hour(self._weather)

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
    def __init__(self, 
                 battery: DCCoupledBattery, 
                 weather: Weather,
                 panels: Panel,
                 p_min: float, 
                 p_max: float = 800, 
        ):
        self._battery = battery
        self._forecast = EnergyForecast(
            weather=weather,
            panels=panels,
        )
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

        self._battery.output_power = target_W
        return 