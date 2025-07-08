from abc import ABC, abstractmethod
from ctrlsolar.io.io import Sensor, Consumer
import logging

__all__ = ["Inverter"]

logger = logging.getLogger(__name__)

class Inverter(ABC):
    @abstractmethod
    def get_production(self) -> float | None:
        """Method to get the current production in [W]"""
        pass

    @abstractmethod
    def get_production_limit(self) -> float | None:
        """Method to get current production limit in [W]"""
        pass

    @abstractmethod
    def set_production_limit(self, limit: float):
        """Method to set the current limit in [W]"""
        pass