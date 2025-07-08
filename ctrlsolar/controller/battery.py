from ctrlsolar.inverter import Inverter
from ctrlsolar.battery import Battery
from ctrlsolar.controller import Controller
import logging

logger = logging.getLogger(__name__)


class BatteryModeFromSoC(Controller):
    def __init__(self, battery: Battery, load_first_soc: float):
        self.load_first_soc = load_first_soc
        self.battery = battery

    def update(self):
        if self.battery.state_of_charge > self.load_first_soc:
            if self.battery.get_mode() != "load_first":
                self.battery.set_mode("load_first")
                logger.info("Switched Battery to `load_first`.")
        else:
            if self.battery.get_mode() != "battery_first":
                self.battery.set_mode("battery_first")
                logger.info("Switched Battery to `battery_first`.")

        return