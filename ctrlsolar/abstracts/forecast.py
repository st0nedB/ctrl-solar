from abc import ABC, abstractmethod
import pandas as pd

class Forecast(ABC):
    @abstractmethod
    def get(self) -> pd.DataFrame:
        pass