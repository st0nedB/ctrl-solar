import requests
import pandas as pd
from pvlib.location import Location # type:ignore
from datetime import datetime, timedelta
import logging
from typing import TypedDict, cast
from ctrlsolar.panels.abstract import Weather

logger = logging.getLogger(__name__)


class _OpenMeteoHourly(TypedDict):
    time: list[str]
    diffuse_radiation: list[float]
    direct_normal_irradiance: list[float]
    global_tilted_irradiance: list[float]
    shortwave_radiation: list[float]


class _OpenMeteoResponse(TypedDict):
    hourly: _OpenMeteoHourly


class OpenMeteoWeather(Weather):
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
        self._forecast: pd.DataFrame | None = None
        self._forecast_age: datetime | None = None

    def _get_forecast(self, date: str):
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.latitude}&longitude={self.longitude}&"
            "hourly=diffuse_radiation,direct_normal_irradiance,global_tilted_irradiance,shortwave_radiation&"
            f"timezone={self.timezone}&start_date={date}&end_date={date}"
        )

        response: requests.Response = requests.get(weather_url)
        data = cast(_OpenMeteoResponse, response.json())
        hourly: _OpenMeteoHourly = data["hourly"]

        times: pd.DatetimeIndex = pd.to_datetime(hourly["time"])
        dhi: pd.Series[float] = pd.Series(hourly["diffuse_radiation"], index=times)
        dni: pd.Series[float] = pd.Series(hourly["direct_normal_irradiance"], index=times)
        gti: pd.Series[float] = pd.Series(hourly["global_tilted_irradiance"], index=times)
        ghi: pd.Series[float] = pd.Series(hourly["shortwave_radiation"], index=times)

        solpos = self.location.get_solarposition(times)
        df: pd.DataFrame = pd.DataFrame(
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
        today = datetime.now().today().strftime("%Y-%m-%d")

        if self._forecast is None or self._forecast_age is None:
            self._forecast = self._get_forecast(date=today)
            self._forecast_age = datetime.now()

        if datetime.now() - self._forecast_age > self.update_every:
            self._forecast = self._get_forecast(date=today)
            self._forecast_age = datetime.now()

        return self._forecast