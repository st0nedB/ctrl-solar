from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "DCCoupledBattery",
]


class DCCoupledBattery(ABC):
    max_power: int  # in [W]
    serial_number: str  # battery serial number

    @property
    @abstractmethod
    def n_batteries(self) -> int | None:
        pass

    @property
    @abstractmethod
    def capacity(self) -> int:
        pass

    @property
    @abstractmethod
    def energy_out(self) -> float:
        pass

    @property
    @abstractmethod
    def online(self) -> int:
        pass

    @property
    @abstractmethod
    def state_of_charge(self) -> float | None:
        pass

    @property
    @abstractmethod
    def discharge_limit(self) -> float | None:    
        pass

    @property
    @abstractmethod
    def charge_limit(self) -> float | None:    
        pass

    @property
    @abstractmethod
    def output_power(self) -> float | None:
        pass

    @output_power.setter
    @abstractmethod
    def output_power(self, power: int | float) -> None:
        pass    

    @property
    @abstractmethod
    def energy_charged(self) -> float | None:
        pass

    @property
    @abstractmethod
    def energy_missing(self) -> float | None:
        pass