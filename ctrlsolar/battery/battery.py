from abc import ABC, abstractmethod
from ctrlsolar.panels.panels import Panel
from typing import Literal
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

__all__ = [
    "Battery",
    "DCCoupledBattery",
]


class Battery(ABC):
    max_power: int  # in [W]
    capacity: int  # in [Wh]
    serial_number: str  # battery serial number

    @property
    @abstractmethod
    def state_of_charge(self) -> float | None:
        pass

    @property
    @abstractmethod
    def full(self) -> bool | None:
        pass

    @property
    @abstractmethod
    def empty(self) -> bool | None:
        pass

    @property
    @abstractmethod
    def remaining_charge(self) -> float | None:
        pass

    @property
    @abstractmethod
    def output_power(self) -> float | None:
        pass

    @property
    @abstractmethod
    def discharge_power(self) -> float | None:
        pass

    @property
    @abstractmethod
    def charge_power(self) -> float | None:
        pass


class DCCoupledBattery(Battery):
    def __init__(self, serial: str, panels: list[Panel]):
        self.serial_number = serial
        self.panels = panels
        self._modes = {
            0: "load_first",
            1: "battery_first",
        }

    @property
    def panel_forecast(self) -> list[pd.DataFrame] | None:
        return [panel.forecast for panel in self.panels]

    @property
    def predicted_production_by_hour(self) -> pd.Series:
        return pd.concat([panel.predicted_production_by_hour for panel in self.panels], axis=1).sum(axis=1)

    def predicted_production_end_hour(self, threshold_kWh: float = 0.2) -> int:
        production_end = self.predicted_production_by_hour > threshold_kWh*1E3
        last_production_time = production_end[::-1].idxmax().time()  # type: ignore -> idx is a time
        last_production_hour = int(last_production_time.strftime("%H"))

        return last_production_hour

    def predicted_production_start_hour(self, threshold_kWh: float = 0.2) -> int:
        production_start = self.predicted_production_by_hour > threshold_kWh*1E3
        first_production_time = production_start.idxmax().time()  # type: ignore -> idx is a time
        first_production_hour = int(first_production_time.strftime("%H"))

        return first_production_hour

    def predicted_remaining_production(self):
        current_time = datetime.now().time()
        total_production = self.predicted_production_by_hour
        remaining_production = total_production[pd.to_datetime(total_production.index).time >= current_time]

        return remaining_production.sum()

    @property
    @abstractmethod
    def solar_power(self) -> float | None:
        pass

    @property
    @abstractmethod
    def mode(self) -> str | None:
        pass

    @mode.setter
    @abstractmethod
    def mode(self, mode: Literal["battery_first", "load_first"]):
        pass