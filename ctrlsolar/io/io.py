from abc import ABC, abstractmethod
from collections import deque
from typing import Any

class Sensor(ABC):
    def __init__(self, buffer_len: int = 1000):
        self._buffer = deque(buffer_len * [None], maxlen=buffer_len)
    
    @abstractmethod
    def get(self) -> Any:
        pass
    
    @property
    def buffer(self) -> list:
        return list(self._buffer)

class Consumer(ABC):
    @abstractmethod
    def set(self, value: Any):
        pass