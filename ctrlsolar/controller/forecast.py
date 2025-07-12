import requests
import pandas as pd
from pvlib.location import Location
from pvlib.irradiance import get_total_irradiance
from datetime import datetime, timedelta
from ctrlsolar.io.io import Sensor
from ctrlsolar.controller.controller import Controller
import logging

logger = logging.getLogger(__name__)


class OpenMeteoForecast:
    def __init__(self, latitude: float, longitude: float, timezone: str):
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.location = Location(latitude, longitude, tz=timezone)

    def get_forecast(self, date):
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.latitude}&longitude={self.longitude}&"
            "hourly=diffuse_radiation,direct_normal_irradiance,global_tilted_irradiance,shortwave_radiation&"
            f"timezone={self.timezone}&start_date={date}&end_date={date}"
        )

        response = requests.get(weather_url)
        data = response.json()
        hourly = data["hourly"]

        times = pd.to_datetime(hourly["time"])
        dhi = pd.Series(hourly["diffuse_radiation"], index=times)
        dni = pd.Series(hourly["direct_normal_irradiance"], index=times)
        gti = pd.Series(hourly["global_tilted_irradiance"], index=times)
        ghi = pd.Series(hourly["shortwave_radiation"], index=times)

        solpos = self.location.get_solarposition(times)
        df = pd.DataFrame(
            {
                "times": times,
                "GHI": ghi,
                "DNI": dni,
                "DHI": dhi,
                "GTI": gti,
                "apparent_zenith": solpos["apparent_zenith"],
                "azimuth": solpos["azimuth"],
            }
        )

        return df


class Panel:
    def __init__(
        self,
        surface_tilt: float,
        surface_azimuth: float,
        panel_area: float,
        panel_efficiency: float,
    ):
        """Initialize a Solar Panel

        Args:
            surface_tilt (float): Tilting angle of the panel in degree (0 - No tilt, 90 - tilted upwards)
            surface_azimuth (float): Azimuth direction of panel in degree, 0 = North, 90 = East, 180 = South, 270 = West
            area (float): Size of the panel in [m^2]
            efficiency (float): Efficiency of the panel, 0-1.

        """
        self.surface_tilt = surface_tilt
        self.surface_azimuth = surface_azimuth
        self.panel_area = panel_area
        self.panel_efficiency = panel_efficiency

    def predict_production(self, forecast: pd.DataFrame) -> float:

        poa = get_total_irradiance(
            surface_tilt=self.surface_tilt,
            surface_azimuth=self.surface_azimuth,
            solar_zenith=forecast["apparent_zenith"],
            solar_azimuth=forecast["azimuth"],
            dni=forecast["DNI"],
            ghi=forecast["GHI"],
            dhi=forecast["DHI"],
        )
        p_dc = poa["poa_global"] * self.panel_area * self.panel_efficiency  # in W

        return p_dc.sum()


class ProductionForecast(Controller):
    name: str = "ProductionForecast"

    def __init__(
        self, panels: list[Panel], weather: OpenMeteoForecast, sensor_today: Sensor, max_age: timedelta = timedelta(hours=1)
    ):
        self.weather = weather
        self.panels = panels
        self.sensor_today = sensor_today
        self.max_age = max_age
        self._weather_forecast = None
        self._weather_forecast_from = None

    def forecast_at(self, date):
        if self._weather_forecast is None:
            self._weather_forecast = self.weather.get_forecast(date)
            self._weather_forecast_from = datetime.now()
        else:
            if self._weather_forecast_from is not None:
                if datetime.now() - self._weather_forecast_from > self.max_age:
                    self._weather_forecast = self.weather.get_forecast(date)
            else:
                self._weather_forecast = self.weather.get_forecast(date)
                self._weather_forecast_from = datetime.now()

        weather = self._weather_forecast
        p_dcs = [x.predict_production(weather) for x in self.panels]

        return sum(p_dcs)

    def production_today(self):
        return self.sensor_today.get()

    def update(self):
        today = datetime.now().today().strftime("%Y-%m-%d")
        forecast = self.forecast_at(today)
        until_now = self.production_today()
        forecast_age = (datetime.now() - self._weather_forecast_from).total_seconds() // 60 if self._weather_forecast_from is not None else "N/A"

        logger.info(f"--------")
        logger.info(f"Production Forecast for {today} (age: {forecast_age:.0f} minutes)")
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
