from abc import ABC, abstractmethod
from ctrlsolar.panels.panels import Panel
import pandas as pd
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "Battery",
    "DCCoupledBattery",
]


class Battery(ABC):
    max_power: int  # in [W]
    capacity: int  # in [Wh]

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
    def output_power_limit(self) -> float | None:
        pass

    @output_power_limit.setter
    @abstractmethod
    def output_power_limit(self, power: float):
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
    def __init__(self, panels: list[Panel]):
        self.panels = panels

    @property
    def panel_forecast(self) -> list[pd.DataFrame] | None:
        return [panel.forecast for panel in self.panels]

    def predicted_production_by_hour(self) -> list[pd.DataFrame] | None:
        return [panel.predicted_production_by_hour for panel in self.panels]

    def predicted_production_end_hour(self, threshold_W: float = 50.0) -> int:
        production_end = pd.concat(
            [panel.predicted_production_by_hour > threshold_W for panel in self.panels],
            axis=1,
        ).apply(all, axis=1)
        last_production_time = production_end[::-1].idxmax().time()  # type: ignore -> idx is a time
        last_production_hour = int(last_production_time.strftime("%H"))

        return last_production_hour

    def predicted_production_start_hour(self, threshold_W: float = 50.0) -> int:
        production_end = pd.concat(
            [panel.predicted_production_by_hour > threshold_W for panel in self.panels],
            axis=1,
        ).apply(all, axis=1)
        first_production_time = production_end.idxmax().time()  # type: ignore -> idx is a time
        first_production_hour = int(first_production_time.strftime("%H"))

        return first_production_hour

    @property
    @abstractmethod
    def solar_power(self) -> float | None:
        pass