from __future__ import annotations

import json

from ctrlsolar.config import FilterConfig, SensorConfig
from ctrlsolar.functions import filter_dict_with_keys
from ctrlsolar.io import ExponentialSmoothing, Mqtt, MqttSensor
from ctrlsolar.io.filters import AverageSmoothing


def build_powermeter_sensor(
    config: SensorConfig, mqtt: Mqtt, loop_interval: int
):
    sensor = MqttSensor(
        mqtt=mqtt,
        topic=config.topic,
        filter=_build_filter(config.filter),
    )

    if config.smoothing is None:
        return sensor

    last_k = config.smoothing.last_k
    if last_k is None:
        source_interval = config.smoothing.source_interval or loop_interval
        last_k = max(1, loop_interval // source_interval)

    if config.smoothing.kind == "average":
        return AverageSmoothing(sensor=sensor, last_k=last_k)

    return ExponentialSmoothing(sensor=sensor, last_k=last_k)


def _build_filter(config: FilterConfig):
    return lambda payload: filter_dict_with_keys(
        json.loads(payload),
        dkeys=config.path,
        dtype=config.dtype,  # type: ignore[arg-type]
        scale=config.scale,
    )
