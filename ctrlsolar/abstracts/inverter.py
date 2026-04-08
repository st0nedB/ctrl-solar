from abc import ABC, abstractmethod
from ctrlsolar.abstracts.battery import DCCoupledBattery
from typing import Optional
import logging

__all__ = ["Inverter"]

logger = logging.getLogger(__name__)

class Inverter(ABC):
    battery: Optional[DCCoupledBattery] = None

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

    @property
    @abstractmethod
    def energy_today(self) -> float | None:
        """Method to return today's energy production [kWh]"""

    @production_limit.setter
    @abstractmethod
    def production_limit(self, limit: float):
        """Method to set the current limit in [W]"""
        pass