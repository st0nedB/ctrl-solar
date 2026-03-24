from ctrlsolar.abstracts.battery import DCCoupledBattery
from ctrlsolar.abstracts.io import Sensor
from ctrlsolar.io.mqtt import MqttSensor
from ctrlsolar.io.filters import AverageSmoothing
from typing import Optional, Any
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
        n_batteries_stacked: int = 1,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.soc_sensor = state_of_charge_sensor
        self.mode_sensor = mode_sensor
        self.output_power_sensor = output_power_sensor
        self.charge_power_sensor = charge_power_sensor
        self.discharge_power_sensor = discharge_power_sensor
        self.solar_sensor = solar_sensor
        self.capacity = n_batteries_stacked * 2048  # raw capacity in Wh

    @property
    def state_of_charge(self) -> float | None:
        return self.soc_sensor.get()

    @property
    def discharge_power(self) -> float | None:
        return self.discharge_power_sensor.get()

    @property
    def charge_power(self) -> float | None:
        return self.charge_power_sensor.get()

    @property
    def output_power(self) -> float | None:
        return self.output_power_sensor.get()

    @property
    def solar_power(self) -> float | None:
        return self.solar_sensor.get()

    @classmethod
    def initialize_from_grobro(
        cls,
        serial: str,
        n_batteries_stacked: int = 1,
        use_smoothing: bool = False,
        last_k: Optional[int] = None,
    ) -> DCCoupledBattery:
        if use_smoothing:
            if last_k is None:
                raise ValueError(
                    f"Found `use_smoothing=True. Smoothing requires values for `last_k` but found None."
                )
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
        if use_smoothing:
            output_power_sensor = AverageSmoothing(
                sensor=output_power_sensor, last_k=last_k  # type: ignore
            )
        solar_sensor = MqttSensor(
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=[lambda y: (lambda x: float(x) if x is not None else None)(  # type: ignore
                json.loads(y)["pv_tot_power"]  # type: ignore
            )],
        )
        if use_smoothing:
            solar_sensor = AverageSmoothing(
                sensor=solar_sensor, last_k=last_k  # type: ignore
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
        if use_smoothing:
            charge_power_sensor = AverageSmoothing(
                sensor=charge_power_sensor, last_k=last_k  # type: ignore
            )

        return cls(
            serial=serial,
            state_of_charge_sensor=state_of_charge_sensor,
            output_power_sensor=output_power_sensor,
            solar_sensor=solar_sensor,
            mode_sensor=mode_sensor,
            discharge_power_sensor=discharge_power_sensor,
            charge_power_sensor=charge_power_sensor,
            n_batteries_stacked=n_batteries_stacked,
        )
