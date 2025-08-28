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
        self._end_prod_switch = False

    def _reset_before_sunrise(self):
        now_hour = int(datetime.now().today().strftime("%H"))
        production_start_hours = min(
            [battery.predicted_production_start_hour() for battery in self.batteries]
        )
        if now_hour >= production_start_hours - 1:
            if self._last_reset < datetime.now().date():
                self._last_reset = datetime.now().date()
                self._end_prod_switch = False
                for battery in self.batteries:
                    battery.mode = "load_first"
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

    @property
    def n_load_first(self) -> int:
        return sum([bb.mode == "load_first" for bb in self.batteries])

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
            current_hour = int(datetime.now().strftime("%H"))
            production_ends = [
                bb.predicted_production_end_hour(threshold_kWh=0.2)
                for bb in self.batteries
            ]

            for battery, prod_end in zip(self.batteries, production_ends):
                # production is ongoing for this battery
                if current_hour < prod_end:
                    if not battery.empty:
                        if self.n_load_first > 1:
                            battery.mode = "battery_first"

            # production has ended for all batteries
            if current_hour >= max(production_ends):
                if not self._end_prod_switch:
                    self._end_prod_switch = True
                    for battery in self.batteries:
                        battery.mode = "battery_first"

                # find the indices which sort the batteries by their available solar power
                solar_powers = [battery.solar_power for battery in self.batteries]
                sort_idx = [
                    x for x, y in sorted(enumerate(solar_powers), key=lambda x: x[1])  # type: ignore
                ]

                for idx in sort_idx:
                    battery = self.batteries[idx]
                    if not battery.empty:
                        battery.mode = "load_first"
                        logger.info(f"Switched battery {idx} to mode `load_first`.")
                        break

            logger.info(
                f"Detected more than one battery discharging over threshold of {self.discharge_threshold} W."
            )

        empty = [battery.empty for battery in self.batteries]
        if all(empty):
            logger.info(f"All batteries are empty.")

        return
