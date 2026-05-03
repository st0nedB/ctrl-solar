from ctrlsolar.mqtt.mqtt import MqttSensor

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
