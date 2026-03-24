from abc import ABC, abstractmethod
import logging

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
    def __init__(self, serial: str):
        self.serial_number = serial

    @property
    @abstractmethod
    def solar_power(self) -> float | None:
        pass
