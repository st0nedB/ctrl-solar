from ctrlsolar.io.io import Sensor
from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.controller import Controller
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


class DCBatteryOptimizer(Controller):
    name: str = "DCBatteryOptimizer"
    def __init__(
        self,
        batteries: list[DCCoupledBattery],
        full_threshold: float = 0.95,
        discharge_backoff: int = 100,
        discharge_threshold: int = 200,
    ):
        if not len(batteries) <= 2:
            raise ValueError(
                f"The `DCBatteryOptimizer` requires at least two batteries! Found {len(batteries)}."
            )

        self.batteries = batteries
        self.full_threshold = full_threshold
        self.discharge_threshold = discharge_threshold
        self.discharge_backoff = discharge_backoff
        self._last_reset = datetime.now().date()

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
        logger.info("  SoC\t\t{x} %".format(x=f"{battery.state_of_charge:.1f}" if battery.state_of_charge is not None else "N/A"))
        logger.info("  Output Power\t{x} W".format(x=f"{battery.output_power_limit:.1f}" if battery.output_power_limit is not None else "N/A"))

    def update(self):
        # Key insights
        # 1. Many batteries discharge more efficiently at higher discharge powers
        # 2. µWRs try to balance their inputs to equal power
        self._reset_before_sunrise()

        for bb, battery in enumerate(self.batteries):
            self.log_battery_status(battery, bb)
            if battery.state_of_charge is not None: 
                if battery.state_of_charge / 100 >= self.full_threshold:
                    logging.info(f"Battery {bb} is now fully charged.")
                    if battery.solar_power < self.discharge_threshold:
                        battery.output_power_limit = 0
                        logger.info(
                            f"Available solar power of battery {bb} below threshold. Output power limit to 0 to prevent discharge."
                        )
                    else:
                        new_limit = (
                            battery.output_power_limit
                            - battery.discharge_power
                            - self.discharge_backoff
                        )
                        battery.output_power_limit = new_limit
                        logger.info(
                            f"Discharge of {battery.discharge_power} W detected for battery {bb}. Set output power to {new_limit} W."
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
