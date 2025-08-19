from ctrlsolar.io.io import Sensor
from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.controller import Controller
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)

# TODO:
# This controller is not useful as long as the work_mode can't be changed programatically


class DCBatteryOptimizer(Controller):
    def __init__(
        self,
        batteries: tuple[DCCoupledBattery],
        full_threshold: float = 0.95,
        demand_threshold: int = 100,
        discharge_threshold: int = 200,
    ):
        if not len(batteries) < 2:
            raise ValueError(
                f"The `DCBatteryOptimizer` requires at least two batteries! Found {len(batteries)}."
            )

        self.batteries = batteries
        self.full_threshold = full_threshold
        self.demand_threshold = demand_threshold
        self.discharge_threshold = discharge_threshold
        self._last_reset = datetime.now().date()
        self._trackers = [deque(20 * [0], maxlen=20) for _ in self.batteries]

    def _reset_before_sunrise(self):
        now_hour = int(datetime.now().today().strftime("%H"))
        production_start_hours = min(
            [battery.predicted_production_start_hour() for battery in self.batteries]
        )
        if now_hour >= production_start_hours - 1:
            if self._last_reset < datetime.now().date():
                self._last_reset = datetime.now().date()
                for battery in self.batteries:
                    battery.output_power_limit = battery.max_power
        return

    def log_battery_status(self, battery: DCCoupledBattery, idx: int):
        logger.info(f"Battery {idx}")
        logger.info(f"  SoC\t\t{battery.state_of_charge:.1f} %")
        logger.info(f"  Output Power\t{battery.output_power_limit:.1f} W")

    def update(self):
        self._reset_before_sunrise()

        # Key insights
        # 1. Many batteries discharge more efficiently at higher discharge powers
        # 2. µWRs try to balance their inputs to equal power

        # batteries start their day in load_first @ 800W
        # once full, they set their output power to the current solar_w - 100
        # if not enough solar power is less than 200 W (or some threshold) for a defined interval) -> output_power = 0 W
        # we do this for all batteries, step by step
        # the last one will discharge until empty
        # once that battery is depleted, we switch the next one back to "load_first" @ 800W
        # at sunrise, we switch all batteries back to "load_first" @ 800W (new cycle)
        # so in each iteration we check if a battery is above is full (based on the threshold). If so switch its output_power to solar_w - 100

        for bb, (battery, solar_pow) in enumerate(zip(self.batteries, self._trackers)):
            avg_solar = sum(solar_pow) / len(solar_pow)

            if battery.state_of_charge >= self.full_threshold:
                logging.info(f"Battery {bb} is now fully charged.")
                if battery.solar_power < self.discharge_threshold:
                    battery.output_power_limit = 0
                    logger.info(
                        f"Available solar power of battery {bb} below threshold. Output power limit to 0 to prevent discharge."
                    )
                else:
                    battery.output_power_limit = avg_solar - self.demand_threshold
                    logger.info(
                        f"Average solar power of {avg_solar} W detected for battery {bb}. Set output power to {avg_solar - self.demand_threshold} W."
                    )

        off = [battery.output_power_limit == 0 for battery in self.batteries]
        if all(off):
            logger.warning(f"All DC-Batteries are switched off!")
            for battery in reversed(self.batteries):
                if not battery.empty:
                    if battery.output_power_limit == 0:
                        battery.output_power_limit = battery.max_power
                        logger.info(
                            f"Found non-empty battery and switched power output to {battery.max_power}."
                        )
                        break

        empty = [battery.empty for battery in self.batteries]
        if all(empty):
            logger.info(f"All batteries are empty.")

        return
