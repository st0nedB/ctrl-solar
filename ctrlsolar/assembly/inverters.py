from __future__ import annotations

from ctrlsolar.assembly.registries import INVERTER_FACTORIES, INVERTER_MODELS
from ctrlsolar.config import InverterConfig
from ctrlsolar.io import Mqtt


def build_inverter(config: InverterConfig, mqtt: Mqtt):
    factory = INVERTER_FACTORIES[config.transport]
    model = INVERTER_MODELS[config.model]
    return factory(
        mqtt=mqtt,
        topic=config.topic_prefix,
        inverter=model,
    )
