from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.controller import Controller
from ctrlsolar.functions import check_properties
from datetime import datetime
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

    def _check_empty_sensors_readings(self) -> bool:
        empty_sensors_readings = []
        for idx, battery in enumerate(self.batteries):
            check = check_properties(battery)
            empty = False
            for key, value in check.items():
                if value is False:
                    empty = True
                    logger.debug(f"Reading of '{key}' is `None` in battery {idx}.")

            if empty:
                logger.warning(f"Found empty sensor readings in battery {idx}.")

            empty_sensors_readings.append(empty)

        logger.debug(f"Sensor check result for batteries is {empty_sensors_readings}.")
        return any(empty_sensors_readings)

    def log_battery_status(self, battery: DCCoupledBattery, idx: int):
        logger.info(f"Battery {idx}")
        logger.info(
            "  SoC\t\t{x} %".format(
                x=(
                    f"{battery.state_of_charge:.1f}"
                    if battery.state_of_charge is not None
                    else "N/A"
                )
            )
        )
        logger.info(
            "  Limit\t\t{x} W".format(
                x=(
                    f"{battery.output_power_limit:.1f}"
                    if battery.output_power_limit is not None
                    else "N/A"
                )
            )
        )
        logger.info(
            "  Solar\t\t{x} W".format(
                x=(
                    f"{battery.solar_power:.1f}"
                    if battery.solar_power is not None
                    else "N/A"
                )
            )
        )
        logger.info(
            "  Output\t{x} W".format(
                x=(
                    f"{battery.output_power:.1f}"
                    if battery.output_power is not None
                    else "N/A"
                )
            )
        )
        logger.info(
            "  Charge\t{x} W".format(
                x=(
                    f"{battery.charge_power:.1f}"
                    if battery.charge_power is not None
                    else "N/A"
                )
            )
        )
        logger.info(
            "  Discharge\t{x} W".format(
                x=(
                    f"{battery.discharge_power:.1f}"
                    if battery.discharge_power is not None
                    else "N/A"
                )
            )
        )

    def update(self):
        # Key insights
        # 1. Many batteries discharge more efficiently at higher discharge powers
        # 2. µWRs try to balance their inputs to equal power
        self._reset_before_sunrise()
        skip_update = True

        if not self._check_empty_sensors_readings():
            skip_update = False
        else:
            logger.warning(
                "Found `None` in one or multiple sensor readings. Update is skipped."
            )

        if not skip_update:
            for bb, battery in enumerate(self.batteries):
                self.log_battery_status(battery, bb)
                if battery.state_of_charge / 100 >= self.full_threshold:  # type: ignore
                    logging.info(f"Battery {bb} is now fully charged.")
                    if battery.solar_power < self.discharge_threshold:  # type: ignore
                        battery.output_power_limit = 0
                        logger.info(
                            f"Available solar power of battery {bb} below threshold. Output power limit to 0 to prevent discharge."
                        )
                    else:
                        new_limit = battery.output_power_limit - battery.discharge_power - self.discharge_backoff  # type: ignore
                        battery.output_power_limit = new_limit
                        logger.info(
                            f"Discharge of {battery.discharge_power} W detected for battery {bb}. Set output power to {new_limit} W."
                        )

            off = [battery.output_power_limit == 0 for battery in self.batteries]
            discharging = [battery.discharge_power > self.discharge_threshold for battery in self.batteries]  # type: ignore

            if sum(discharging) > 1:
                logger.info(
                    f"Detected more than one battery discharging over threshold of {self.discharge_threshold} W."
                )
                # find the indices which sort the batteries by their available solar power
                solar_powers = [battery.solar_power for battery in self.batteries]
                sort_idx = [
                    x for x, y in sorted(enumerate(solar_powers), key=lambda x: x[1])  # type: ignore
                ]

                # switch off the one with the lowest solar power
                for idx in sort_idx:
                    battery = self.batteries[idx]
                    if battery.discharge_power > self.discharge_threshold:  # type: ignore
                        battery.output_power_limit = 0
                        logger.info(f"Stopped discharging on battery {idx}.")
                        break

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
