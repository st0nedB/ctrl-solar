from ctrlsolar.io.io import Sensor
from ctrlsolar.functions import exponential_smoothing
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ExponentialSmoothing(Sensor):
    def __init__(self, sensor: Sensor, last_k: int = 10):
        self.sensor = sensor
        self.values = deque([None] * last_k, maxlen=last_k)

    def get(self) -> float | None:
        self.values.append(self.sensor.get())
        logger.debug(f"Current values in smoothing window:\t {list(self.values)}")
        filtered_values = [v for v in self.values if v is not None]
        if not filtered_values:
            return None

        return exponential_smoothing(filtered_values)


class SumSensor(Sensor):
    def __init__(self, sensors: list[Sensor]):
        self.sensors = sensors

    def get(self) -> float | None:
        values = [sensor.get() for sensor in self.sensors]
        if any(value is None for value in values):
            return None

        return sum(values)
