from datetime import datetime, timedelta
from ctrlsolar.abstracts import Controller, Panel, Forecast, Sensor
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ProductionForecast(Controller):
    name: str = "ProductionForecast"

    def __init__(
        self,
        forecast: Forecast,
        panels: list[Panel],
        energy_today: Sensor,
        max_age: timedelta = timedelta(hours=1),
    ):
        self.forecast = forecast
        self.panels = panels
        self.energy_today = energy_today
        self.max_age = max_age
        self._forecast: pd.DataFrame | None = None
        self._forecast_age = None

    def _update_forecast(self) -> None:
        if self._forecast is None:
            self._forecast = self.forecast.get()
            self._forecast_age = datetime.now()
        else:
            if self._forecast_age is not None:
                if datetime.now() - self._forecast_age > self.max_age:
                    self._forecast = self.forecast.get()
                    self._forecast_age = datetime.now()

        return

    def production_estimate(self) -> float:
        if self._forecast is not None:
            p_dcs = [
                float(x.predicted_production_by_hour(forecast=self._forecast).values.sum()) for x in self.panels
            ]

            return sum(p_dcs)
        
        return 0.

    def update(self):
        self._update_forecast()
        forecast = self.production_estimate()
        until_now = self.energy_today.get() 
        forecast_age = (
            (datetime.now() - self._forecast_age).total_seconds() // 60
            if self._forecast_age is not None
            else "N/A"
        )

        logger.info(f"Production Forecast for today (age: {forecast_age:.0f} minutes)")
        logger.info(
            "Until now\t\t{x}".format(
                x=f"{until_now if until_now is not None else 0.:.2f} kWh"
            )
        )
        logger.info(
            "Estimated\t\t{x}".format(
                x=f"{1E-3*forecast:.2f} kWh"
            )
        )

        return
