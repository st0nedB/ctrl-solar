from abc import ABC, abstractmethod
import pandas as pd

class Panel(ABC):
    @property
    @abstractmethod
    def forecast(self) -> pd.DataFrame:
        pass

    @property
    @abstractmethod
    def predicted_production_by_hour(self) -> pd.DataFrame:
        pass