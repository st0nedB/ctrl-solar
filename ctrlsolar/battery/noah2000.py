from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.io.io import Sensor, Consumer
from ctrlsolar.panels.panels import Panel
from ctrlsolar.io.mqtt import Mqtt, MqttSensor, MqttConsumer
import json
from typing import Optional
import logging

__all__ = ["Noah2000"]

logger = logging.getLogger(__name__)


class Noah2000(DCCoupledBattery):
    max_power: int = 800

    def __init__(
        self,
        state_of_charge_sensor: Sensor,
        mode_sensor: Sensor,
        output_power_sensor: Sensor,
        discharge_power_sensor: Sensor,
        solar_sensor: Sensor,
        charge_limit_sensor: Sensor,
        discharge_limit_sensor: Sensor,
        output_power_consumer: Consumer,
        n_batteries_stacked: int = 1,
        *args,
        **kwargs,
    ):
        super(DCCoupledBattery).__init__(*args, **kwargs)
        self.soc_sensor = state_of_charge_sensor
        self.mode_sensor = mode_sensor
        self.output_power_sensor = output_power_sensor
        self.discharge_power_sensor = discharge_power_sensor
        self.solar_sensor = solar_sensor
        self.charge_limit_sensor = charge_limit_sensor
        self.discharge_limit_sensor = discharge_limit_sensor

        self.output_power_consumer = output_power_consumer
        self.capacity = n_batteries_stacked * 2048

    @property
    def state_of_charge(self) -> float:
        return self.soc_sensor.get()

    @property
    def full(self) -> bool:
        return self.state_of_charge > self.charge_limit_sensor.get()

    @property
    def empty(self) -> bool:
        return self.state_of_charge < self.discharge_limit_sensor.get()

    @property
    def remaining_charge(self) -> float:
        return self.state_of_charge * self.capacity / 100.0

    @property
    def discharge_power(self) -> float:
        return self.discharge_power_sensor.get()
    
    @property
    def solar_power(self) -> float:
        return self.solar_sensor.get()

    @property
    def output_power_limit(self) -> float:
        return self.output_power_sensor.get()

    @output_power_limit.setter
    def output_power_limit(self, power: float):
        if power > self.max_power:
            power = self.max_power
            logger.warning(
                f"Output power target exceeds batteries configured maximum power. Setting power = {self.max_power}."
            )
        data = {
            "charging_limit": self.charge_limit_sensor.get(),
            "discharge_limit": self.discharge_limit_sensor.get(),
            "output_power_w": str(int(power)),
        }

        self.output_power_consumer.set(data)
        return


class NoahMqttFactory:
    @classmethod
    def initialize(
        cls,
        mqtt: Mqtt,
        base_topic: str,
        panels: list[Panel],
        n_batteries_stacked: int = 1,
    ) -> Noah2000:
        state_of_charge_sensor = MqttSensor(
            mqtt=mqtt,
            topic=base_topic,
            filter=lambda y: (lambda x: float(x) if x is not None else 0)(
                json.loads(y)["soc"]
            ),
        )
        mode_sensor = MqttSensor(
            mqtt=mqtt,
            topic=base_topic,
            filter=lambda y: (json.loads(y)["work_mode"]),
        )
        output_power_sensor = MqttSensor(
            mqtt=mqtt,
            topic=base_topic,
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["output_w"]
            ),
        )
        solar_sensor = MqttSensor(
            mqtt=mqtt,
            topic=base_topic,
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["solar_w"]
            ),
        )
        charge_limit_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"{base_topic}/parameters",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["charging_limit"]
            ),
        )
        discharge_limit_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"{base_topic}/parameters",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["discharge_limit"]
            ),
        )
        output_power_consumer = MqttConsumer(
            mqtt=mqtt,
            topic=f"{base_topic}/parameters/set",
        )

        return Noah2000(
            state_of_charge_sensor=state_of_charge_sensor,
            output_power_sensor=output_power_sensor,
            solar_sensor=solar_sensor,
            charge_limit_sensor=charge_limit_sensor,
            discharge_limit_sensor=discharge_limit_sensor,
            output_power_consumer=output_power_consumer,
            n_batteries_stacked=n_batteries_stacked,
            panels=panels,
        )
