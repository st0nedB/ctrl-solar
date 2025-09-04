from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.controller import Controller
from ctrlsolar.functions import check_properties
from datetime import datetime
from typing import Literal
import logging

logger = logging.getLogger(__name__)


class DCBatteryOptimizer(Controller):
    name: str = "DCBatteryOptimizer"

    def __init__(
        self,
        batteries: list[DCCoupledBattery],
        full_threshold: float = 95,
        per_hour_production_threshold_kWh: float = 0.2,
    ):
        super().__init__()
        if len(batteries) < 2:
            raise ValueError(
                f"The `DCBatteryOptimizer` requires at least two batteries! Found {len(batteries)}."
            )

        self.batteries = batteries
        self.full_threshold = full_threshold
        self.per_hour_production_threshold_kWh = per_hour_production_threshold_kWh

    def _get_current_cycle_state(self) -> Literal["pending", "ongoing", "ended"] | None:
        """Determines we are in the daily production cycle based on panel production forecast."""
        current_hour = int(datetime.now().strftime("%H"))
        production_starts = min(
            [
                bb.predicted_production_start_hour(threshold_kWh=self.per_hour_production_threshold_kWh)
                for bb in self.batteries
            ]
        )

        production_ends = max(
            [
                bb.predicted_production_end_hour(threshold_kWh=0.2)
                for bb in self.batteries
            ]
        )

        if 0 <= current_hour < production_starts:
            state = "pending"
        elif production_starts <= current_hour < production_ends:
            state = "ongoing"
        elif production_ends <= current_hour < 24:
            state = "ended"
        else:
            logger.error(
                f"State could not be determined for `current_hour`={current_hour}, `production_starts`={production_starts}, and `production_ends`={production_ends}."
            )
            state = None

        return state

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

        logger.debug(
            f"Sensor check result for batteries is {empty_sensors_readings} (True = Empty Reading)."
        )
        return any(empty_sensors_readings)

    @property
    def n_load_first(self) -> int:
        return sum([bb.mode == "load_first" for bb in self.batteries])
    
    @property
    def n_battery_first(self) -> int:
        return sum([bb.mode == "battery_first" for bb in self.batteries])    

    def log_battery_status(self, battery: DCCoupledBattery, idx: int):
        logger.info(f"Battery {idx} - SN {battery.serial_number}")
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
            "  Mode\t\t{x}".format(
                x=(battery.mode if battery.mode is not None else "N/A")
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
                    f"{abs(battery.discharge_power):.1f}"
                    if battery.discharge_power is not None
                    else "N/A"
                )
            )
        )

    def update(self):
        # Key insights
        # 1. Many batteries discharge more efficiently at higher discharge powers, meaning, conversion losses are minimized if only one battery discharges at a time
        # 2. µWRs try to balance their inputs to equal power, meaning, they will discharge a battery and limit another, even if enough solar is available
        skip_update = True

        if self._check_empty_sensors_readings():
            logger.warning(
                "Found `None` in one or multiple sensor readings. Update is skipped."
            )
        elif all([battery.empty for battery in self.batteries]):
            logger.info(f"All batteries are empty. Update is skipped.")
        else:
            skip_update = False

        cycle = self._get_current_cycle_state()
        if cycle is None:
            logger.warning(f"Current cycle undertermined. Skipping update!")
            skip_update = True
        else:
            logger.info(f"Based on panel forecasts the current cycle is `{cycle}`.")

        logger.info("Pre-Update status summary:")
        for ii, battery in enumerate(self.batteries):
            self.log_battery_status(battery, ii)

        if not skip_update:
            if cycle == "pending":  # production has not started for any battery
                for battery in self.batteries:
                    if battery.mode != "load_first":
                        logger.info(f"Switching all batteries to `load_first` to prepare for new cycle.")
                        battery.mode = "load_first"

            elif cycle == "ongoing":
                # Step 1: Switch fully charged batteries to battery_first (once per day)
                for ii, battery in enumerate(self.batteries):
                    if battery.state_of_charge >= self.full_threshold: # type: ignore
                        if self.n_load_first > 1:
                            logger.info(
                                f"Switching battery {ii} to `battery_first` to prevent discharging during remaining production cycle."
                            )
                            battery.mode = "battery_first"
                            break  # switch only one battery per update to ensure change has time to propagate

            else: # production has ended for all batteries
                for ii, battery in enumerate(self.batteries):
                    if battery.mode != "load_first":
                        logger.debug(
                            f"Switching battery {ii} to `load_first` because production has ended."
                        )
                        battery.mode = "load_first"

        return
