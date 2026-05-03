from ctrlsolar.mqtt.mqtt import MqttSensor
from typing import Type
import json

# Library for specific device implementations
# List of devices:
# - Shelly1PM (via MQTT)

__all__ = ["Shelly1PM_Energy", "Shelly1PM_Power"]


class Shelly1PM_Energy(MqttSensor):
    def __init__(self, topic: str):
        super().__init__(
            topic=f"{topic}/status/switch:0",
            filter=[
                lambda y: (lambda x: float(x) if x is not None else 0)(  # type: ignore
                    json.loads(y)["ret_aenergy"]["total"]  # type: ignore
                )
            ],
        )

    @property
    def energy_out(self) -> float | None:
        return self.value


class Shelly1PM_Power(MqttSensor):
    def __init__(self, topic: str):
        super().__init__(
            topic=f"{topic}/status/switch:0",
            filter=[
                lambda y: (lambda x: -float(x) if x is not None else 0)(  # type: ignore
                    json.loads(y)["apower"]  # type: ignore
                )
            ],
        )

MAPPINGS: dict[str, Type[MqttSensor]] = {
    "Shelly1PM_Energy": Shelly1PM_Energy, 
    "Shelly1PM_Power": Shelly1PM_Power,
}