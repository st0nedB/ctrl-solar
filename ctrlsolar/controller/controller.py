from abc import ABC, abstractmethod

class Controller(ABC):
    name: str 
    
    def __init__(self):
        pass

    @abstractmethod
    def update(self) -> None:
        return