from abc import ABC, abstractmethod

class CalibrationSensor(ABC):
    @property
    @abstractmethod
    def energy(self) -> float:
        pass

    @property
    @abstractmethod
    def power(self) -> float:
        pass