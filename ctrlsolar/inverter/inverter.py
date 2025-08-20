from abc import ABC, abstractmethod
import logging

__all__ = ["Inverter"]

logger = logging.getLogger(__name__)

class Inverter(ABC):
    @property
    @abstractmethod
    def production(self) -> float | None:
        """Method to get the current production in [W]"""
        pass

    @property
    @abstractmethod
    def production_limit(self) -> float | None:
        """Method to get current production limit in [W]"""
        pass

    @production_limit.setter
    @abstractmethod
    def production_limit(self, limit: float):
        """Method to set the current limit in [W]"""
        pass