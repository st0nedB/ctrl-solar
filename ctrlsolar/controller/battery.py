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
        full_threshold: float = 95,
    ):
        super().__init__()
        if len(batteries) < 2:
            raise ValueError(
                f"The `DCBatteryOptimizer` requires at least two batteries! Found {len(batteries)}."
            )

        self.batteries = batteries
        self.full_threshold = full_threshold
        self._last_reset = datetime.now().date()
        self._end_prod_switch = False
        self._daily_full_charge_switches = (
            set()
        )  # Track which batteries were switched due to full charge today

    def _reset_before_sunrise(self):
        now_hour = int(datetime.now().today().strftime("%H"))
        production_start_hours = min(
            [battery.predicted_production_start_hour() for battery in self.batteries]
        )
        if now_hour >= production_start_hours - 1:
            if self._last_reset < datetime.now().date():
                self._last_reset = datetime.now().date()
                self._end_prod_switch = False
                self._daily_full_charge_switches.clear()  # Reset daily tracking
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

        logger.debug(
            f"Sensor check result for batteries is {empty_sensors_readings} (True = Empty Reading)."
        )
        return any(empty_sensors_readings)

    @property
    def n_load_first(self) -> int:
        return sum([bb.mode == "load_first" for bb in self.batteries])

    def log_battery_status(self, battery: DCCoupledBattery, idx: int):
        logger.info(f"Battery {idx} - {battery.serial_number}")
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
                    f"{battery.discharge_power:.1f}"
                    if battery.discharge_power is not None
                    else "N/A"
                )
            )
        )

    def update(self):
        # Key insights
        # 1. Many batteries discharge more efficiently at higher discharge powers, meaning, conversion losses are minimized if only one battery discharges at a time
        # 2. µWRs try to balance their inputs to equal power, meaning, they will discharge a battery and limit another, even if enough solar is available
        self._reset_before_sunrise()
        skip_update = True

        if self._check_empty_sensors_readings():
            logger.warning(
                "Found `None` in one or multiple sensor readings. Update is skipped."
            )
        elif all([battery.empty for battery in self.batteries]):
            logger.info(f"All batteries are empty. Update is skipped.")
        else:
            skip_update = False

        for ii, battery in enumerate(self.batteries):
            self.log_battery_status(battery, ii)

        if not skip_update:
            current_hour = int(datetime.now().strftime("%H"))
            production_ends = [
                bb.predicted_production_end_hour(threshold_kWh=0.2)
                for bb in self.batteries
            ]

            # During production: handle full charge switching and ensure only one battery is in load_first mode
            production_ongoing = any(
                current_hour < prod_end for prod_end in production_ends
            )

            if production_ongoing:
                # Step 1: Switch fully charged batteries to battery_first (once per day)
                for ii, battery in enumerate(self.batteries):
                    if (
                        battery.state_of_charge >= self.full_threshold  # type: ignore
                        and ii not in self._daily_full_charge_switches
                    ):

                        # Count how many would remain in load_first after this switch
                        remaining_load_first = sum(
                            1
                            for jj, bb in enumerate(self.batteries)
                            if bb.mode == "load_first" and jj != ii
                        )

                        # Only switch if at least one other battery will remain in load_first
                        if remaining_load_first > 0:
                            battery.mode = "battery_first"
                            self._daily_full_charge_switches.add(ii)
                            logger.info(f"Battery {ii} mode switched to `battery_first`.")

            # production has ended for all batteries
            if current_hour >= max(production_ends):
                # switch all batteries to `load_first`
                for ii, battery in enumerate(self.batteries):
                    if battery.mode != "load_first":
                        logger.debug(f"Switching battery {ii} to `load_first` because production has ended.")
                        battery.mode = "load_first"

        return
