from abc import ABC, abstractmethod
from typing import Any

class Sensor(ABC):
    @abstractmethod
    def get(self) -> Any:
        pass

class Consumer(ABC):
    @abstractmethod
    def set(self, value: Any):
        pass