from datetime import datetime, timedelta
from ctrlsolar.io.io import Sensor
from ctrlsolar.controller.controller import Controller
from ctrlsolar.panels.panels import Panel
from ctrlsolar.panels.weather import OpenMeteoForecast
import logging

logger = logging.getLogger(__name__)


class ProductionForecast(Controller):
    name: str = "ProductionForecast"

    def __init__(
        self,
        panels: list[Panel],
        weather: OpenMeteoForecast,
        sensor_today: Sensor,
        max_age: timedelta = timedelta(hours=1),
    ):
        self.weather = weather
        self.panels = panels
        self.sensor_today = sensor_today
        self.max_age = max_age
        self._weather_forecast = None
        self._weather_forecast_from = None

    def _update_weather_forecast(self) -> None:
        if self._weather_forecast is None:
            self._weather_forecast = self.weather.get()
            self._weather_forecast_from = datetime.now()
        else:
            if self._weather_forecast_from is not None:
                if datetime.now() - self._weather_forecast_from > self.max_age:
                    self._weather_forecast = self.weather.get()
                    self._weather_forecast_from = datetime.now()

        return

    def production_estimate(self) -> float:
        p_dcs = [
            float(x.predicted_production_by_hour.values.sum()) for x in self.panels
        ]
        return sum(p_dcs)

    def production_today(self):
        return self.sensor_today.get()

    def update(self):
        self._update_weather_forecast()
        forecast = self.production_estimate()
        until_now = self.production_today()
        forecast_age = (
            (datetime.now() - self._weather_forecast_from).total_seconds() // 60
            if self._weather_forecast_from is not None
            else "N/A"
        )

        logger.info(f"--------")
        logger.info(f"Production Forecast for today (age: {forecast_age:.0f} minutes)")
        logger.info(
            "Until now\t\t{x}".format(
                x=f"{1E-3*until_now:.2f} kWh" if until_now is not None else "N/A"
            )
        )
        logger.info(
            "Estimated\t\t{x}".format(
                x=f"{1E-3*forecast:.2f} kWh" if forecast is not None else "N/A"
            )
        )

        return
