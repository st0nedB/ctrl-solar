from abc import ABC, abstractmethod
import requests
import pandas as pd
from pvlib.location import Location
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Forecast(ABC):
    @abstractmethod
    def get(self) -> pd.DataFrame:
        pass


class OpenMeteoForecast(Forecast):
    def __init__(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        update_every: timedelta = timedelta(hours=1),
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.location = Location(latitude, longitude, tz=timezone)
        self.update_every = update_every
        self._forecast = None
        self._forecast_age = None

    def _get_forecast(self):
        today = datetime.now().today().strftime("%Y-%m-%d")
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.latitude}&longitude={self.longitude}&"
            "hourly=diffuse_radiation,direct_normal_irradiance,global_tilted_irradiance,shortwave_radiation&"
            f"timezone={self.timezone}&start_date={today}&end_date={today}"
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

    def get(self) -> pd.DataFrame:
        if self._forecast is None:
            self._forecast = self._get_forecast()
            self._forecast_age = datetime.now()

        if self._forecast_age is not None:
            if datetime.now() - self._forecast_age > self.update_every:
                self._forecast = self._get_forecast()
                self._forecast_age = datetime.now()

        return self._forecast
