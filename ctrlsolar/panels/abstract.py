from abc import ABC, abstractmethod
import pandas as pd


class Weather(ABC):
    @abstractmethod
    def get(self) -> pd.DataFrame:
        pass    

class Panel(ABC):
    @abstractmethod
    def predicted_production_by_hour(self, weather: Weather) -> dict[int, float]:
        pass