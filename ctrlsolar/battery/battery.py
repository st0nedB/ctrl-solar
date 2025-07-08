from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "Battery",
]


class Battery(ABC):
    max_power: float  # in [W]
    capacity: float  # in [Wh]

    @property
    @abstractmethod
    def state_of_charge(self) -> float | None:
        pass

    @property
    @abstractmethod
    def remaining_charge(self) -> float | None:
        pass

    @abstractmethod
    def get_available_power(self) -> float | None:
        pass

    @abstractmethod
    def get_mode(self) -> str | None:
        pass

    @abstractmethod
    def set_mode(self, mode: str):
        pass

    @abstractmethod
    def get_output_power_limit(self) -> float | None:
        pass

    @abstractmethod
    def set_output_power_limit(self, power: float):
        pass
