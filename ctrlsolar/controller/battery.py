from ctrlsolar.io.io import Sensor
from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.controller import Controller
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


class DCBatteryOptimizer(Controller):
    def __init__(
        self,
        batteries: tuple[DCCoupledBattery],
        demand_sensor: Sensor,
        soc_threshold: float = 0.95,
        demand_threshold: int = 100,
    ):
        self.batteries = batteries
        self.soc_threshold = soc_threshold
        self.demand_sensor = demand_sensor
        self.demand_threshold = demand_threshold
        self._change_counter: list[int,] = len(self.batteries) * [1]
        self._current_day = self.today
        self._demand_tracker = deque([False] * 20, maxlen=20)

    @property
    def today(self):
        return datetime.now().today().strftime("%Y-%m-%d")

    def _update_demand(self):
        demand = self.demand_sensor.get() > self.demand_threshold
        self._demand_tracker.append(demand)
        return

    def _reset_on_new_day(self):
        if self._current_day != self.today:
            self._change_counter = len(self.batteries) * [1]
            self._current_day = self.today

        self._demand_tracker = deque([False] * 20, maxlen=20)
        return

    def update(self):
        # Key insights
        # 1. "Battery first" forwards only the available solar power without discharge
        # 2. "Load first" attempts to satisfy the load, including power
        # 3. Many batteries discharge more efficiently at higher discharge powers
        # 4. µWRs try to balance their inputs to equal power

        # batteries start their day in load_first @ 800W
        # once full, they switch to "battery first"
        # if not enough solar power is available anymore (for a defined interval), we switch 1 battery back to "load_first" @ 800W untils its empty (to maximize discharge efficiency) and switch it back to "load_first" @ 800W (new cycle)
        # once that battery is depleted, we switch the next one back to "load_first" @ 800W
        # at sunrise, we switch all batteries back to "load_first" @ 800W (new cycle)

        # so in each iteration we check if a battery is above is full (based on the threshold). If so we switch it to battery first.
        # we limit the amount of switches to n_switch_per_day to avoid ping-ponging
        #

        for bb, battery in enumerate(self.batteries):
            if battery.state_of_charge >= self.soc_threshold:
                logging.info(f"Battery {bb} is now fully charged.")
                if battery.mode == "load_first":
                    if self._change_counter[bb] > 0:
                        battery.mode = "battery_first"
                        self._change_counter[bb] -= 1
                        logging.info(
                            f"Battery {bb} switched to `battery_first` to prevent discharge."
                        )
                        continue
                else:
                    logging.info(
                        f"Battery {bb} mode is already `battery_first`. No mode change necessary."
                    )

        battery_first = [battery.mode == "battery_first" for battery in self.batteries]
        load_first = [battery.mode == "load_first" for battery in self.batteries]

        self._update_demand()
        if all(self._demand_tracker):
            # There is not discharge/excess solar power
            battery_first = [
                battery.mode == "battery_first" for battery in self.batteries
            ]
            if all(battery_first):
                # All batteries are in battery first, but excess solar power is no longer sufficient
                # -> switch the last battery back to provide power
                battery = self.batteries[-1]
                battery.mode = "load_first"
                battery.output_power_limit = 800
            elif any(battery_first):
                # Not all are in battery first, but load_first batteries are empty
                # -> switch the next battery back to load_first
                for battery in reversed(self.batteries):
                    if battery.mode == "battery_first":
                        battery.mode = "load_first"
                        battery.output_power_limit = 800

            elif all(load_first):
                # All are in load_first, but solar power is insufficient to cover demand
                # -> switch all batteries where production has ended into battery_first to prevent inefficient discharge
                current_hour = int(datetime.now().today().strftime("%H"))
                production_ends_by_hours = [
                    battery.predicted_production_end_hour()
                    for battery in self.batteries
                ]
                sorted_indices = [
                    index
                    for index, value in sorted(
                        enumerate(production_ends_by_hours), key=lambda x: x[1]
                    )
                ]

                for idx in sorted_indices[:-1]:
                    battery = self.batteries[idx]
                    if battery.empty:
                        # don't change mode of empty batteries
                        continue

                    if battery.predicted_production_end_hour() <= current_hour:
                        battery.mode = "battery_first"
                        self._change_counter[idx] -= 1
                        logging.info(
                            f"Battery {idx} switched to `battery_first` to prevent inefficient discharge."
                        )

                #   - All batteries are empty and in load_first again, ready for the next cycle
                #   - The next cycle starts but one battery is still full (battery_first)
                #       -> do nothing, can continue to be full

        # There is enough excess solar power
        #   -> Do nothing
        return
