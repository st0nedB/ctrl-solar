from ctrlsolar.controller import Controller
from ctrlsolar.inverter import Inverter
from ctrlsolar.battery import Battery

class BatterySaver(Controller):
    """A controller for the Inverter which considers Battery state."""
    def __init__(self, inverter: Inverter, battery: Battery):
        self.inverter = inverter
        self.battery = battery
        
    def update(self):
        