from abc import ABC, abstractmethod
import pandas as pd

class Weather(ABC):
    @abstractmethod
    def get(self) -> pd.DataFrame:
        pass