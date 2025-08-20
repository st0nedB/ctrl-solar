from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.io.io import Sensor, Consumer
from ctrlsolar.panels.panels import Panel
from ctrlsolar.io.mqtt import Mqtt, MqttSensor, MqttConsumer
import json
import logging

__all__ = ["Noah2000", "NoahMqttFactory"]

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
        super().__init__(*args, **kwargs)
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
    def state_of_charge(self) -> float | None:
        return self.soc_sensor.get()

    @property
    def mode(self) -> str | None:
        mode = self.mode_sensor.get()
        if mode == "battery_first":
            raise ValueError(
                f"Unsupported battery mode `{self.mode}` detected. Battery must be in `load_first` mode."
            )

        return mode

    @property
    def full(self) -> bool | None:
        full = None
        if self.state_of_charge is not None:
            if self.charge_limit is not None:
                full = self.state_of_charge > self.charge_limit

        return full

    @property
    def empty(self) -> bool | None:
        empty = None
        if self.state_of_charge is not None:
            if self.discharge_limit is not None:
                empty = self.state_of_charge < self.discharge_limit

        return empty

    @property
    def remaining_charge(self) -> float | None:
        soc = self.state_of_charge
        cap = self.capacity
        result = None
        if (soc is not None) and (cap is not None):
            result = soc * cap / 100.0

        return result

    @property
    def discharge_power(self) -> float | None:
        return self.discharge_power_sensor.get()

    @property
    def solar_power(self) -> float | None:
        return self.solar_sensor.get()

    @property
    def output_power_limit(self) -> float | None:
        return self.output_power_sensor.get()

    @property
    def discharge_limit(self) -> float | None:
        return self.discharge_limit_sensor.get()

    @property
    def charge_limit(self) -> float | None:
        return self.charge_limit_sensor.get()

    @property
    def output_power(self) -> float | None:
        return self.output_power_sensor.get()

    def _build_valid_payload(self, power: float) -> dict | None:
        data = None
        if self.discharge_limit is not None:
            if self.charge_limit is not None:
                data = {
                    "charging_limit": self.charge_limit,
                    "discharge_limit": self.discharge_limit,
                    "output_power_w": str(int(power)),
                }

        return data

    @output_power_limit.setter
    def output_power_limit(self, power: float):
        if power > self.max_power:
            power = self.max_power
            logger.warning(
                f"Output power target exceeds batteries configured maximum power. Setting power = {self.max_power}."
            )

        data = self._build_valid_payload(power=power)
        if data is not None:
            self.output_power_consumer.set(data)
        else:
            logger.warning(
                f"Could not construct valid payload due to `None` readings from `discharge` and/or `charge` sensor."
            )

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
        discharge_power_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"{base_topic}",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["discharge_w"]
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
            mode_sensor=mode_sensor,
            discharge_limit_sensor=discharge_limit_sensor,
            discharge_power_sensor=discharge_power_sensor,
            charge_limit_sensor=charge_limit_sensor,
            output_power_consumer=output_power_consumer,
            n_batteries_stacked=n_batteries_stacked,
            panels=panels,
        )
