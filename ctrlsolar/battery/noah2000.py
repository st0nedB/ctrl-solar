from ctrlsolar.battery.abstract import DCCoupledBattery
from ctrlsolar.mqtt.abstract import Sensor, Consumer
from ctrlsolar.mqtt.mqtt import MqttSensor, MqttConsumer
from typing import Any
import json
import logging

__all__ = ["Noah2000"]

logger = logging.getLogger(__name__)


class Noah2000(DCCoupledBattery):
    max_power: int = 800

    def __init__(
        self,
        serial_number: str,
        online_sensor: Sensor,
        state_of_charge_sensor: Sensor,
        discharge_limit_sensor: Sensor, 
        charge_limit_sensor: Sensor, 
        output_power_sensor: Sensor,
        output_power_consumer: Consumer,
        panel_power_sensor: Sensor,
        n_batteries_sensor: Sensor,
        energy_out_sensor: Sensor,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.serial_number = serial_number
        self._online_sensor = online_sensor
        self._soc_sensor = state_of_charge_sensor
        self._discharge_limit_sensor=discharge_limit_sensor
        self._charge_limit_sensor=charge_limit_sensor
        self._output_power_sensor = output_power_sensor
        self._output_power_consumer = output_power_consumer
        self._panel_power_sensor = panel_power_sensor
        self._n_batteries_sensor = n_batteries_sensor
        self._energy_out = energy_out_sensor

    @property
    def online(self) -> bool:
        return self._online_sensor.value

    @property
    def capacity(self) -> int:
        return self.n_batteries*2048

    @property
    def n_batteries(self) -> int:
        n = self._n_batteries_sensor.value
        if n is None:
            n = 1
        return n
    
    @property
    def energy_out(self) -> float:
        return self._energy_out.value

    @property
    def state_of_charge(self) -> float | None:
        return self._soc_sensor.value
    
    @property
    def discharge_limit(self) -> float | None:
        return self._discharge_limit_sensor.value
    
    @property
    def charge_limit(self) -> float | None:
        return self._charge_limit_sensor.value

    @property
    def output_power(self) -> float | None:
        return self._output_power_sensor.value
    
    @output_power.setter
    def output_power(self, power: int | float) -> None:
        self._output_power_consumer.set(power) 
        return
    
    @property
    def energy_charged(self) -> float | None:
        if self.state_of_charge is None: 
            return None 
        
        return self.state_of_charge * self.capacity
    
    @property
    def panel_power(self) -> float | None:
        return self._panel_power_sensor.value
    
    @property
    def energy_missing(self) -> float | None:
        if self.energy_charged is None:
            return None 
        
        return self.capacity - self.energy_charged

    @classmethod
    def from_grobro(
        cls,
        serial: str,
    ) -> DCCoupledBattery:
        online_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/availability",
            filter=[lambda x: True if str(x)=="online" else False if not None else False], # type:ignore
        )
        state_of_charge_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) / 100 if x is not None else 0)(  # type: ignore
                json.loads(y)["tot_bat_soc_pct"]  # type: ignore
            )],
        )
        discharge_limit_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) / 100 if x is not None else 0)(  # type: ignore
                json.loads(y)["discharge_limit"]  # type: ignore
            )],
        )
        charge_limit_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) / 100 if x is not None else 0)(  # type: ignore
                json.loads(y)["charge_limit"]  # type: ignore
            )],
        )
        output_power_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) if x is not None else None)(  # type: ignore
                json.loads(y)["out_power"]  # type: ignore
            )],
        )
        output_power_consumer = MqttConsumer(
            topic=f"homeassistant/number/grobro/{serial.upper()}/slot1_power/set"
        )
        panel_power_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) if x is not None else None)(  # type: ignore
                json.loads(y)["pv_tot_power"]  # type: ignore
            )],
        )
        n_battery_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (  # type: ignore
                lambda x: (
                    1
                    if x is None else int(x)
                )
            )(
                json.loads(y)["bat_cnt"]  # type: ignore
            )],  # type: ignore
        )
        energy_out_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: 1E3*float(x) if x is not None else None)(  # type: ignore
                json.loads(y)["eng_out_device"]  # type: ignore
            )],
        )

        return cls(
            serial_number=serial,
            online_sensor=online_sensor,
            state_of_charge_sensor=state_of_charge_sensor,
            discharge_limit_sensor=discharge_limit_sensor,
            charge_limit_sensor=charge_limit_sensor,
            output_power_sensor=output_power_sensor,
            output_power_consumer=output_power_consumer,
            panel_power_sensor=panel_power_sensor,
            n_batteries_sensor=n_battery_sensor,
            energy_out_sensor=energy_out_sensor,
        )
        
