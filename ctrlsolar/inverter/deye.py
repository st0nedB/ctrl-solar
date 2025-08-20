from ctrlsolar.inverter.inverter import Inverter
from ctrlsolar.io.io import Sensor, Consumer
from ctrlsolar.io.mqtt import Mqtt, MqttSensor, MqttConsumer

__all__ = ["DeyeSunM160G4", "Deye2MqttFactory"]

class DeyeSun(Inverter):
    max_power: float = 1600.0
    limit_per: float = 50.0
    def __init__(
        self,
        power_sensor: Sensor,
        production_limit_sensor: Sensor,
        production_limit_consumer: Consumer,
    ):
        self.power_sensor = power_sensor
        self.production_limit_sensor = production_limit_sensor
        self.production_limit_consumer = production_limit_consumer
        return

    @property
    def production(self) -> float | None:
        return self.power_sensor.get()

    @property
    def production_limit(self) -> float | None:
        reading = self.production_limit_sensor.get()
        if reading is None: 
            return None

        limit_per = float(reading) / 100
        return self.max_power * limit_per

    @production_limit.setter
    def production_limit(self, limit: float):
        limit_per = round((limit / self.max_power) * 100)
        if limit_per < 1:
            limit_per = 1

        if limit_per > self.limit_per:
            limit_per = self.limit_per

        return self.production_limit_consumer.set(str(limit_per))

class DeyeSunM160G4(DeyeSun):
    max_power: float = 1600.0
    limit_per: float = 50.0

class Deye2MqttFactory:
    @classmethod
    def initialize(
        cls, mqtt: Mqtt, base_topic: str, inverter: type[DeyeSun]
    ) -> Inverter:
        power_sensor=MqttSensor(
            mqtt=mqtt,
            topic=f"{base_topic}/ac/active_power",
            filter=lambda x: float(x) if x is not None else None,
        )
        production_limit_sensor=MqttSensor(
            mqtt=mqtt,
            topic=f"{base_topic}/settings/active_power_regulation",
            filter=lambda x: float(x) if x is not None else None,
        )
        production_limit_consumer=MqttConsumer(
            mqtt=mqtt, topic=f"{base_topic}/settings/active_power_regulation/command"
        )
        return inverter(
            power_sensor=power_sensor,
            production_limit_sensor=production_limit_sensor,
            production_limit_consumer=production_limit_consumer,
        )