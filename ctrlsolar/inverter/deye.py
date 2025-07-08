from ctrlsolar.inverter.inverter import Inverter
from ctrlsolar.io.io import Sensor, Consumer

__all__ = ["DeyeSunM160G4"]

class DeyeSunM160G4(Inverter):
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

    def get_production(self) -> float | None:
        return self.power_sensor.get()

    def get_production_limit(self) -> float | None:
        reading = self.production_limit_sensor.get()
        if reading is None: 
            return None

        limit_per = float() / 100
        return self.max_power * limit_per

    def set_production_limit(self, limit: float):
        limit_per = round((limit / self.max_power) * 100)
        if limit_per < 1:
            limit_per = 1

        if limit_per > self.limit_per:
            limit_per = self.limit_per

        return self.production_limit_consumer.set(str(limit_per))
