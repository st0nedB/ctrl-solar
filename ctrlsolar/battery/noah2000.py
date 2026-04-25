from ctrlsolar.battery.abstract import DCCoupledBattery
from ctrlsolar.mqtt.abstract import Sensor
from ctrlsolar.mqtt.mqtt import MqttSensor
from typing import Any
import json
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
        charge_power_sensor: Sensor,
        discharge_power_sensor: Sensor,
        solar_sensor: Sensor,
        n_batteries_sensor: Sensor,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._soc_sensor = state_of_charge_sensor
        self._mode_sensor = mode_sensor
        self._output_power_sensor = output_power_sensor
        self._charge_power_sensor = charge_power_sensor
        self._discharge_power_sensor = discharge_power_sensor
        self._solar_sensor = solar_sensor
        self._n_batteries_sensor = n_batteries_sensor

    @property
    def capacity(self) -> int:
        return self.n_batteries*2048

    @property
    def n_batteries(self) -> int:
        n = self._n_batteries_sensor.get()
        if n is None:
            n = 1
        return n

    @property
    def state_of_charge(self) -> float | None:
        return self._soc_sensor.get()

    @property
    def discharge_power(self) -> float | None:
        return self._discharge_power_sensor.get()

    @property
    def charge_power(self) -> float | None:
        return self._charge_power_sensor.get()

    @property
    def output_power(self) -> float | None:
        return self._output_power_sensor.get()

    @property
    def solar_power(self) -> float | None:
        return self._solar_sensor.get()
    
    @property
    def energy_charged(self) -> float | None:
        if self.state_of_charge is None: 
            return None 
        
        return self.state_of_charge * self.capacity
    
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
        state_of_charge_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) / 100 if x is not None else 0)(  # type: ignore
                json.loads(y)["tot_bat_soc_pct"]  # type: ignore
            )],
        )
        mode_sensor = MqttSensor(
            topic=f"homeassistant/number/grobro/{serial.upper()}/slot1_mode/get",
            filter=[lambda x: int(x) if x is not None else None],  # type: ignore
        )
        output_power_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) if x is not None else None)(  # type: ignore
                json.loads(y)["out_power"]  # type: ignore
            )],
        )
        solar_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) if x is not None else None)(  # type: ignore
                json.loads(y)["pv_tot_power"]  # type: ignore
            )],
        )
        discharge_power_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (  # type: ignore
                lambda x: (
                    0
                    if x is not None and float(x) > 0
                    else (float(x) if x is not None else None)
                )
            )(
                json.loads(y)["charging_discharging"]  # type: ignore
            )],  # type: ignore
        )
        charge_power_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (  # type: ignore
                lambda x: (
                    0
                    if x is not None and float(x) < 0
                    else (float(x) if x is not None else None)
                )
            )(
                json.loads(y)["charging_discharging"]  # type: ignore
            )],  # type: ignore
        )
        n_battery_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/bat_cnt",
            filter=[lambda x: int(x) if x is not None else None] # type:ignore
        )

        return cls(
            serial=serial,
            state_of_charge_sensor=state_of_charge_sensor,
            output_power_sensor=output_power_sensor,
            solar_sensor=solar_sensor,
            mode_sensor=mode_sensor,
            discharge_power_sensor=discharge_power_sensor,
            charge_power_sensor=charge_power_sensor,
            n_batteries_sensor=n_battery_sensor,
        )
