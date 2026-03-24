from ctrlsolar.abstracts.inverter import Inverter
from ctrlsolar.abstracts.io import Sensor, Consumer
from ctrlsolar.io.mqtt import MqttSensor, MqttConsumer

__all__ = ["DeyeSunM160G4"]

class DeyeSun(Inverter):
    max_power: float = 1600.0
    limit_per: float = 50.0
    def __init__(
        self,
        power_sensor: Sensor,
        production_limit_sensor: Sensor,
        energy_today_sensor: Sensor,
        production_limit_consumer: Consumer,
    ):
        self.power_sensor = power_sensor
        self.production_limit_sensor = production_limit_sensor
        self.energy_today_sensor = energy_today_sensor
        self.production_limit_consumer = production_limit_consumer
        return

    @property
    def production(self) -> float | None:
        return self.power_sensor.get()
    
    @property
    def energy_today(self) -> float | None:
        return self.energy_today_sensor.get()

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
    
    @classmethod
    def initialize_from_deye2mqtt(
        cls, topic: str,
    ) -> Inverter:
        power_sensor=MqttSensor(
            topic=f"{topic}/ac/active_power",
            filter=[lambda x: float(x) if x is not None else None,],   # type: ignore
        )
        production_limit_sensor=MqttSensor(
            topic=f"{topic}/settings/active_power_regulation",
            filter=[lambda x: float(x) if x is not None else None,],   # type: ignore
        )
        energy_today_sensor=MqttSensor(
            topic=f"{topic}/day_energy",
            filter=[lambda x: float(x) if x is not None else None,],   # type: ignore
        )
        production_limit_consumer=MqttConsumer(
            topic=f"{topic}/settings/active_power_regulation/command"
        )
        return cls(
            power_sensor=power_sensor,
            production_limit_sensor=production_limit_sensor,
            energy_today_sensor=energy_today_sensor,
            production_limit_consumer=production_limit_consumer,
        )    

class DeyeSunM160G4(DeyeSun):
    max_power: float = 1600.0
    limit_per: float = 50.0
