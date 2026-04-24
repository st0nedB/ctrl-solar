from abc import ABC, abstractmethod
import pandas as pd

class Panel(ABC):
    @abstractmethod
    def predicted_production_by_hour(self, weather: pd.DataFrame) -> pd.DataFrame:
        pass