from ctrlsolar.io.io import Sensor
from ctrlsolar.functions import exponential_smoothing
from collections import deque
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class ExponentialSmoothing(Sensor):
    def __init__(self, sensor: Sensor, last_k: int = 10):
        self.sensor = sensor
        self.last_k = last_k
        self._smooth_func = exponential_smoothing

    @property
    def buffer(self) -> list:
        return list(self.sensor.buffer)

    def get(self) -> float | None:
        logger.debug(
            f"Last {self.last_k} values in sensor buffer:\t {list(self.buffer[-self.last_k:])}"
        )
        filtered_values = [v for v in self.buffer[-self.last_k :] if v is not None]
        if not filtered_values:
            return None

        return self._smooth_func(filtered_values)


class AverageSmoothing(ExponentialSmoothing):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._smooth_func = lambda x: sum(x) / len(x)


class SumSensor(Sensor):
    def __init__(self, sensors: list[Sensor], filter: Callable = lambda x: x):
        self.sensors = sensors
        self.filter = filter

    def get(self) -> float | None:
        values = [sensor.get() for sensor in self.sensors]
        if any(value is None for value in values):
            return None

        return self.filter(sum(values))


class PropertySensor(Sensor):
    def __init__(self, instance: object, property: str, filter: Callable = lambda x: x):
        self.instance = instance
        self.property = property
        self.filter = filter

    def get(self) -> float | None:
        val = getattr(self.instance, self.property)
        return self.filter(val)
