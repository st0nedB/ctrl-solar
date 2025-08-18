from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.io.io import Sensor, Consumer
from ctrlsolar.panels.panels import Panel
from typing import Optional
import logging

__all__ = ["Noah2000"]

logger = logging.getLogger(__name__)


class Noah2000(DCCoupledBattery):
    max_power: float = 800
    mode_mapping = {"battery_first": "battery_first", "load_first": "load_first"}

    def __init__(
        self,
        state_of_charge_sensor: Sensor,
        mode_sensor: Sensor,
        output_power_sensor: Sensor,
        solar_sensor: Sensor,
        charge_limit_sensor: Sensor,
        discharge_limit_sensor: Sensor,
        mode_consumer: Consumer,
        output_power_consumer: Consumer,
        n_batteries_stacked: int = 1,
        *args,
        **kwargs,
    ):
        super(DCCoupledBattery).__init__(*args, **kwargs)
        self.soc_sensor = state_of_charge_sensor
        self.mode_sensor = mode_sensor
        self.output_power_sensor = output_power_sensor
        self.solar_sensor = solar_sensor
        self.charge_limit_sensor = charge_limit_sensor
        self.discharge_limit_sensor = discharge_limit_sensor

        self.mode_consumer = mode_consumer
        self.output_power_consumer = output_power_consumer

        self.capacity = n_batteries_stacked * 2048

    @property
    def state_of_charge(self) -> float:
        return self.soc_sensor.get()

    @property
    def full(self) -> bool:
        return self.state_of_charge > self.charge_limit_sensor.get()

    @property
    def empty(self) -> bool:
        return self.state_of_charge < self.discharge_limit_sensor.get()

    @property
    def remaining_charge(self) -> float:
        return self.state_of_charge * self.capacity / 100.0

    @property
    def available_power(self) -> float:
        if self.state_of_charge > self.discharge_limit_sensor.get():
            return self.max_power
        else:
            solar_prod = self.solar_sensor.get()
            if solar_prod > 0:
                return solar_prod
            else:
                return 0.0

    @property
    def mode(self) -> str:
        mode = self.mode_sensor.get()
        return mode

    @mode.setter
    def mode(self, mode: str):
        if self.mode_consumer is not None:
            if mode not in self.supported_modes:
                logger.error(f"Unsupported mode {mode}. Not setting!")
            self.mode_consumer.set(mode)
        return

    @property
    def output_power_limit(self) -> float:
        if self.mode_sensor.get() == "load_first":
            return self.output_power_sensor.get()

        return self.max_power

    @output_power_limit.setter
    def output_power_limit(self, power: float):
        if power > self.max_power:
            power = self.max_power
            logger.warning(
                f"Output power target exceeds batteries configured maximum power. Setting power = {self.max_power}."
            )

        self.output_power_consumer.set(power)
        return
