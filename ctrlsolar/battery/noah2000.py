from ctrlsolar.battery.battery import DCCoupledBattery
from ctrlsolar.io.io import Sensor, Consumer
from ctrlsolar.panels.panels import Panel
from ctrlsolar.io.mqtt import Mqtt, MqttSensor, MqttConsumer
from ctrlsolar.io.filters import AverageSmoothing
from typing import Literal, Optional
import json
import logging

__all__ = ["Noah2000", "GroBroFactory"]

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
        charge_limit_sensor: Sensor,
        discharge_limit_sensor: Sensor,
        todays_production_sensor: Sensor,
        total_production_sensor: Sensor,
        mode_consumer: Consumer,
        n_batteries_stacked: int = 1,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.soc_sensor = state_of_charge_sensor
        self.mode_sensor = mode_sensor
        self.output_power_sensor = output_power_sensor
        self.charge_power_sensor = charge_power_sensor
        self.discharge_power_sensor = discharge_power_sensor
        self.solar_sensor = solar_sensor
        self.charge_limit_sensor = charge_limit_sensor
        self.discharge_limit_sensor = discharge_limit_sensor
        self.todays_production_sensor = todays_production_sensor
        self.total_production_sensor = total_production_sensor
        self.mode_consumer = mode_consumer
        self.capacity = n_batteries_stacked * 2048  # raw capacity in Wh

    @property
    def state_of_charge(self) -> float | None:
        return self.soc_sensor.get()

    @property
    def mode(self) -> str | None:
        val = self.mode_sensor.get()
        if val is None:
            return None

        return self._modes[val]

    @mode.setter
    def mode(self, mode: Literal["battery_first", "load_first"]):
        if self.mode != mode:
            numeric_mode = None
            for k, v in self._modes.items():
                if v == mode:
                    numeric_mode = k
                    break

            if numeric_mode is not None:
                logger.debug(f"Setting new mode `{mode}` ({numeric_mode}).")
                self.mode_consumer.set(numeric_mode)
            else:
                logger.warning(f"Mode {mode} is not supported! Skipping set.")

        logger.debug(f"New mode is identical to current mode. Skipping update.")
        return

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
    def charge_power(self) -> float | None:
        return self.charge_power_sensor.get()

    @property
    def solar_power(self) -> float | None:
        return self.solar_sensor.get()

    @property
    def discharge_limit(self) -> float | None:
        return self.discharge_limit_sensor.get()

    @property
    def charge_limit(self) -> float | None:
        return self.charge_limit_sensor.get()

    @property
    def todays_production(self) -> float | None:
        return self.todays_production_sensor.get()

    @property
    def total_production(self) -> float | None:
        return self.total_production_sensor.get()

    @property
    def output_power(self) -> float | None:
        return self.output_power_sensor.get()


class GroBroFactory:
    @classmethod
    def initialize(
        cls,
        mqtt: Mqtt,
        serial: str,
        panels: list[Panel],
        n_batteries_stacked: int = 1,
        use_smoothing: bool = False,
        last_k: Optional[int] = None,
    ) -> Noah2000:
        if use_smoothing:
            if (last_k is None):
                raise ValueError(
                    f"Found `use_smoothing=True. Smoothing requires values for `last_k` but found None."
                )

        state_of_charge_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (lambda x: float(x) if x is not None else 0)(
                json.loads(y)["tot_bat_soc_pct"]
            ),
        )
        mode_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (json.loads(y)["priority_mode"]),
        )
        output_power_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["out_power"]
            ),
        )
        if use_smoothing:
            output_power_sensor = AverageSmoothing(
                sensor=output_power_sensor,
                last_k=last_k  # type: ignore
            )
        solar_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["pv_tot_power"]
            ),
        )
        if use_smoothing:
            solar_sensor = AverageSmoothing(
                sensor=solar_sensor,
                last_k=last_k  # type: ignore
            )
        discharge_power_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (
                lambda x: (
                    0
                    if x is not None and float(x) > 0
                    else (float(x) if x is not None else None)
                )
            )(json.loads(y)["charging_discharging"]),
        )
        charge_power_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (
                lambda x: (
                    0
                    if x is not None and float(x) < 0
                    else (float(x) if x is not None else None)
                )
            )(json.loads(y)["charging_discharging"]),
        )
        if use_smoothing:
            charge_power_sensor = AverageSmoothing(
                sensor=charge_power_sensor,
                last_k=last_k  # type: ignore
            )
        charge_limit_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["charge_limit"]
            ),
        )
        discharge_limit_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["discharge_limit"]
            ),
        )
        todays_production_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (lambda x: 1e3 * float(x) if x is not None else None)(
                json.loads(y)["pv_eng_today"]
            ),
        )
        total_production_sensor = MqttSensor(
            mqtt=mqtt,
            topic=f"homeassistant/grobro/{serial.upper()}/state",
            filter=lambda y: (lambda x: 1e3 * float(x) if x is not None else None)(
                json.loads(y)["eng_out_device"]
            ),
        )
        mode_consumer = MqttConsumer(
            mqtt=mqtt,
            topic=f"homeassistant/number/grobro/{serial.upper()}/slot1_mode/set",
        )

        return Noah2000(
            state_of_charge_sensor=state_of_charge_sensor,
            output_power_sensor=output_power_sensor,
            solar_sensor=solar_sensor,
            mode_sensor=mode_sensor,
            discharge_limit_sensor=discharge_limit_sensor,
            discharge_power_sensor=discharge_power_sensor,
            charge_power_sensor=charge_power_sensor,
            charge_limit_sensor=charge_limit_sensor,
            todays_production_sensor=todays_production_sensor,
            total_production_sensor=total_production_sensor,
            mode_consumer=mode_consumer,
            n_batteries_stacked=n_batteries_stacked,
            panels=panels,
        )
