from datetime import datetime
from ctrlsolar.panels.abstract import Weather, Panel
from ctrlsolar.battery.abstract import DCCoupledBattery
from ctrlsolar.controller.abstract import Controller
from ctrlsolar.controller.forecast import EnergyForecast
from ctrlsolar.controller.monitor import EnergyMonitor
from ctrlsolar.localization import get_timezone
from ctrlsolar.mqtt.mqtt import get_mqtt
from ctrlsolar.mqtt.abstract import Sensor
from ctrlsolar.mqtt.topics import TOPICS
from ctrlsolar.utils import any_is_none
from typing import Optional, Type, cast
import logging

logger = logging.getLogger(__name__)
    
class EnergyController(Controller):
    name: str = "EnergyController"
    _fallback: int = 100

    def __init__(
        self,
        battery: DCCoupledBattery,
        weather: Weather,
        panels: Panel,
        p_min: float,
        p_max: float = 800,
        energy_sensor: Optional[Type[Sensor]] = None
    ):
        self._battery = battery
        self._deviceid = battery.serial_number
        self._forecast = EnergyForecast(
            weather=weather,
            panels=panels,
            device_id=self._battery.serial_number
        )
        self._monitor = EnergyMonitor(
            battery=battery, 
            ac_sensor=energy_sensor,
        )
        self._p_min = p_min
        self._p_max = p_max

        self._battery_hours = []
        self._production_hours = []
        self._last_phase = None
        self._last_target_power = None
        self._last_updated_at = None
        self._last_error = None

        return
    
    def publish_set_power(self, power: int):
        mqtt = get_mqtt()
        mqtt.publish(
            TOPICS["set_power_state"].format(device_id=self._battery.serial_number), power
        )
        return

    def evaluate_day_schedule(self) -> None:
        energy = self._forecast.hourly_production_estimates()
        prod_start = [x > self._p_min for x in energy].index(True)
        prod_end = 24 - [x < self._p_min for x in energy[::-1]].index(False)

        self._production_hours = [*range(prod_start, prod_end)]
        self._battery_hours = [h for h in range(24) if h not in self._production_hours]

        return

    def evaluate_production_power_target(self) -> int | None:
        if any_is_none(self._battery.panel_power, self._battery.energy_missing):
            logger.warning("Found `None` in sensors. Skipping update!")
            return
        
        panel_power = cast(float, self._battery.panel_power)
        missing_Wh = cast(float, self._battery.energy_missing)
        target_W = None

        prod_remaining_h = self._forecast.remaining_production_hours_today(
            cutoff_energy_kWh=self._p_min * 1
        )  # *1h
        if prod_remaining_h == 0:
            prod_remaining_h = 1
        if prod_remaining_h < 0:
            logger.info("Production has already seized. Skipping.")
            return 

        prod_remaining_Wh = self._forecast.remaining_energy_production_today(
            remaining_hours=prod_remaining_h
        )
        next_hour_expected_Wh = self._forecast.next_hour_production_estimate()

        target_W = min(
            (prod_remaining_Wh - missing_Wh) / prod_remaining_h,    # required to ensure batteryies are full
            self._p_max,                                            # the max allowed
            next_hour_expected_Wh / 1,  # /1h                       # the average of the current hour
            panel_power                                             # the maximum available
        )

        target_W = int((target_W // 10) * 10)

        return target_W

    def evaluate_battery_power_target(self) -> int | None:
        if any_is_none(self._battery.energy_charged, self._battery.discharge_limit):
            logger.warning("Found `None` in sensors. Skipping update!")
            return 
        
        energy_charged = cast(float, self._battery.energy_charged)
        discharge_limit = cast(float, self._battery.discharge_limit)

        charge = (
            energy_charged
            - discharge_limit * self._battery.capacity
        )
        
        target_W = charge / len(self._battery_hours)
        logger.info(
            f"Maxmimum sustainable discharge power until next production period is {target_W:.2f} W."
        )
        
        target_W = max(target_W, self._p_min)
        logger.info(f"Evaluated power result is {target_W:.2f} W.")
        target_W = int((target_W // 10) * 10)

        return target_W
    
    def _update_subs(self):
        self._forecast.update()
        self._monitor.update()
        return 

    def update(self):
        self._last_error = None
        try:
            hour = datetime.now(get_timezone()).hour
            self.evaluate_day_schedule()

            if hour in self._battery_hours:
                logger.info(
                    f"Hour {hour}/24, which is battery mode."
                )
                self._last_phase = "battery"
                target_W = self.evaluate_battery_power_target()

            elif hour in self._production_hours:
                logger.info(
                    f"Hour {hour}/24, which is production mode."
                )
                self._last_phase = "production"
                target_W = self.evaluate_production_power_target()

            else:
                logger.warning(
                    f"Failed to determine Phase. Setting fallback power of {self._fallback:.2f} W."
                )
                self._last_phase = "fallback"
                target_W = self._fallback

            self._last_target_power = target_W

            if self._battery.online:
                if target_W is not None:
                    target_W = int(max(target_W, self._p_min))
                    self._last_target_power = target_W
                    logger.info(f"Power-target is evaluated to {target_W:.2f} W. Updated maximum power to {target_W} W.")
                    print(target_W)
                    self._battery.output_power = target_W
                    self.publish_set_power(target_W)
            else:
                logger.info(f"Battery is offline! Skipping update.")

            self._update_subs()
        except Exception as exc:
            self._last_error = str(exc)
            raise
        finally:
            self._last_updated_at = datetime.now(get_timezone()).isoformat(timespec="seconds")

        return

    def snapshot(self) -> dict:
        return {
            "timestamp": datetime.now(get_timezone()).isoformat(timespec="seconds"),
            "controller": {
                "phase": self._last_phase,
                "last_target_power_w": self._last_target_power,
                "last_updated_at": self._last_updated_at,
                "last_error": self._last_error,
            },
            "battery": {
                "serial_number": self._battery.serial_number,
                "online": self._read(lambda: self._battery.online),
                "state_of_charge": self._read(lambda: self._battery.state_of_charge),
                "output_power_w": self._read(lambda: self._battery.output_power),
                "panel_power_w": self._read(lambda: self._battery.panel_power),
                "energy_charged_wh": self._read(lambda: self._battery.energy_charged),
                "energy_missing_wh": self._read(lambda: self._battery.energy_missing),
                "capacity_wh": self._read(lambda: self._battery.capacity),
                "n_batteries": self._read(lambda: self._battery.n_batteries),
                "charge_limit": self._read(lambda: self._battery.charge_limit),
                "discharge_limit": self._read(lambda: self._battery.discharge_limit),
                "energy_out_wh": self._read(lambda: self._battery.energy_out),
            },
            "forecast": self._read(self._forecast.snapshot),
            "actuals": self._read(self._monitor.snapshot),
        }

    def _read(self, getter):
        try:
            return getter()
        except Exception:
            return None

    def set_calibration(self, factors: list[float]) -> None:
        self._forecast.set_calibration(factors)
