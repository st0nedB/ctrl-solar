from datetime import datetime
from ctrlsolar.panels.abstract import Weather, Panel
from ctrlsolar.battery.abstract import DCCoupledBattery
from ctrlsolar.controller.abstract import Controller
from ctrlsolar.mqtt.mqtt import get_mqtt
from ctrlsolar.mqtt.topics import TOPICS, HOURLY_FORECAST_TOPIC_TEMPLATE
import logging

logger = logging.getLogger(__name__)


class EnergyForecast:
    def __init__(
        self,
        weather: Weather,
        panels: Panel,
    ):
        self._weather = weather
        self._panels = panels

    def daily_production_estimate(self) -> float:
        p_dcs = sum(self.hourly_production_estimates())
        return p_dcs

    def hourly_production_estimates(self) -> list[float,]:
        return list(self._panels.predicted_production_by_hour(self._weather).values())

    def next_hour_production_estimate(self) -> float:
        hour = datetime.now().hour
        return self._panels.predicted_production_by_hour(self._weather)[hour]

    def remaining_energy_production_today(self, remaining_hours: int) -> float:
        hour = datetime.now().hour
        energy = sum(self.hourly_production_estimates()[hour : hour + remaining_hours])
        return energy

    def remaining_production_hours_today(self, cutoff_energy_kWh: float) -> int:
        hour = datetime.now().hour
        energy = self.hourly_production_estimates()[hour:]
        index = [x < cutoff_energy_kWh for x in energy].index(True)
        return index

    def publish_forecast(self, device_id: str):
        mqtt = get_mqtt()
        energy = self.hourly_production_estimates()
        energy = [round(x, 2) for x in energy]
        # Publish each hour to its own topic as a numeric value (Wh).
        for hour, value in enumerate(energy):
            topic = HOURLY_FORECAST_TOPIC_TEMPLATE.format(device_id=device_id, hour=hour)
            mqtt.publish(topic, value)
        return


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
    ):
        self._battery = battery
        self._forecast = EnergyForecast(
            weather=weather,
            panels=panels,
        )
        self._p_min = p_min
        self._p_max = p_max

        self._battery_hours = []
        self._production_hours = []

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
        missing_Wh = self._battery.energy_missing
        target_W = None
        if missing_Wh is not None:
            prod_remaining_h = self._forecast.remaining_production_hours_today(
                cutoff_energy_kWh=self._p_min * 1
            )  # *1h
            prod_remaining_Wh = self._forecast.remaining_energy_production_today(
                remaining_hours=prod_remaining_h
            )
            next_hour_expected_Wh = self._forecast.next_hour_production_estimate()

            target_W = min(
                (prod_remaining_Wh - missing_Wh) / prod_remaining_h,
                self._p_max,
                next_hour_expected_Wh / 1,  # /1h
            )

            target_W = int((target_W // 10) * 10)
        else:
            logger.warning(
                f"Missing information about battery charge state.  Skipping!"
            )

        return target_W

    def evaluate_battery_power_target(self) -> int | None:
        charge = (
            self._battery.energy_charged
            - self._battery.discharge_limit * self._battery.capacity
        )
        target_W = None
        if charge is not None:
            target_W = charge / len(self._battery_hours)
            logger.info(
                f"Maxmimum sustainable discharge power until next production period is {target_W} W."
            )
            target_W = max(target_W, self._p_min)
            logger.info(f"Evaluated power result is {target_W} W.")
            target_W = int((target_W // 10) * 10)
        else:
            logger.warning(f"Missing information about battery charge state. Skipping!")

        return target_W

    def update(self):
        hour = datetime.now().hour
        self.evaluate_day_schedule()
        self._forecast.publish_forecast(device_id=self._battery.serial_number)

        if hour in self._battery_hours:
            target_W = self.evaluate_battery_power_target()
            logger.info(
                f"Hour {hour}/24, which is battery mode. Power-target is evaluated to {target_W} W."
            )

        elif hour in self._production_hours:
            target_W = self.evaluate_production_power_target()
            logger.info(
                f"Hour {hour}/24, which is production mode. Power-target is evaluated to {target_W} W."
            )

        else:
            logger.warning(
                f"Failed to determine Phase. Setting fallback power of {self._fallback} W."
            )
            target_W = self._fallback

        if self._battery.online:
            if target_W is not None:
                logger.info(f"Updated maximum power to {target_W} from {int(self._battery.output_power)}.")  # type: ignore
                self._battery.output_power = target_W
                self.publish_set_power(target_W)
        else:
            logger.info(f"Battery is offline! Skipping update.")

        return
