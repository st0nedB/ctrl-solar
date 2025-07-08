from ctrlsolar.battery.battery import Battery
from ctrlsolar.io.io import Sensor, Consumer
from typing import Optional
import logging

__all__ = ["Noah2000"]

logger = logging.getLogger(__name__)


class Noah2000(Battery):
    max_power: float = 800
    min_soc: float = 10.0
    max_soc: float = 100.0
    supported_modes = ["load_first", "battery_first"]

    def __init__(
        self,
        state_of_charge_sensor: Sensor,
        mode_sensor: Sensor,
        output_power_sensor: Sensor,
        solar_sensor: Sensor,
        mode_consumer: Optional[Consumer] = None,
        output_power_consumer: Optional[Consumer] = None,
        n_batteries: int = 1,
    ):
        self.soc_sensor = state_of_charge_sensor
        self.mode_sensor = mode_sensor
        self.mode_consumer = mode_consumer
        self.output_power_sensor = output_power_sensor
        self.output_power_consumer = output_power_consumer
        self.solar_sensor = solar_sensor
        self.capacity = n_batteries * 2048

    @property
    def state_of_charge(self) -> float | None:
        return self.soc_sensor.get()

    @property
    def remaining_charge(self) -> float | None:
        if self.state_of_charge is None:
            return None

        return self.state_of_charge * self.capacity / 100.0

    def get_available_power(self) -> float | None:
        if self.state_of_charge is None:
            return None

        if self.state_of_charge > self.min_soc:
            return self.max_power
        else:
            solar_prod = self.solar_sensor.get()
            if solar_prod > 0:
                return solar_prod
            else:
                return 0.0

    def get_mode(self) -> str | None:
        if self.state_of_charge is None:
            return None

        mode = self.mode_sensor.get()
        return mode

    def set_mode(self, mode: str):
        if self.mode_consumer is not None:
            if mode not in self.supported_modes:
                logger.error(f"Unsupported mode {mode}. Not setting!")
            self.mode_consumer.set(mode)
        return

    def get_output_power_limit(self) -> float:
        return self.output_power_sensor.get()

    def set_output_power_limit(self, power: float):
        if self.output_power_consumer is not None:
            if power > self.max_power:
                power = self.max_power
                logger.warning(
                    f"Output power target exceeds batteries configured maximum power. Setting power = {self.max_power}."
                )

            self.output_power_consumer.set(power)
        return
