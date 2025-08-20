from ctrlsolar.io.io import Sensor
from ctrlsolar.functions import (
    asymmetric_exponential_smoothing,
    compute_asymmetric_alphas,
)
from collections import deque
import logging
import time

logger = logging.getLogger(__name__)


class AsymmetricExponentialSmoothing(Sensor):
    def __init__(self, sensor: Sensor, last_k: int = 10):
        self.sensor = sensor
        self.values = deque([None] * last_k, maxlen=last_k)
        self._interval = deque([0.] * last_k, maxlen=last_k)
        self._last_read = time.time()

    @property
    def sample_interval(self) -> float:
        filtered = [v for v in self._interval if v != 0]
        n_val = 1 if len(filtered) == 0 else len(filtered)
        interval = sum(filtered) / n_val
        logger.debug(f"Current sampling interval is {interval:.4f} s.")
        return interval

    def _update_interval(self) -> None:
        now = time.time()
        self._interval.append(now - self._last_read)
        self._last_read = now
        logger.debug(f"Sampling Intervals are {list(self._interval)}")
        return

    def get(self) -> float | None:
        self.values.append(self.sensor.get())
        self._update_interval()
        logger.debug(f"Current values in smoothing window:\t {list(self.values)}")
        filtered_values = [v for v in self.values if v is not None]
        if not filtered_values:
            return None

        alpha_up, alpha_down = compute_asymmetric_alphas(
            self.sample_interval,
        )
        smoothed = asymmetric_exponential_smoothing(
            filtered_values, alpha_up=alpha_up, alpha_down=alpha_down
        )
        return smoothed
