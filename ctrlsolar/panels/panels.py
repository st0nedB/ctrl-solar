from pvlib.irradiance import get_total_irradiance
from ctrlsolar.panels.weather import OpenMeteoForecast
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Panel:
    def __init__(
        self,
        area: float,
        efficiency: float,
        tilt: float,
        azimuth: float,
        forecast: OpenMeteoForecast,
        calibration: Optional[list[float]] = None,
    ):
        """Initialize a Solar Panel

        Args:
            tilt (float): Tilting angle of the panel in degree (0 - No tilt, 90 - tilted upwards)
            azimuth (float): Azimuth direction of panel in degree, 0 = North, 90 = East, 180 = South, 270 = West
            area (float): Size of the panel in [m^2]
            efficiency (float): Efficiency of the panel, 0-1.
        """
        self.tilt = tilt
        self.azimuth = azimuth
        self.area = area
        self.efficiency = efficiency
        self._forecast = forecast
        self.calibration = calibration if calibration is not None else 24 * [1]

    @property
    def forecast(self):
        return self._forecast.get()

    @property
    def predicted_production_by_hour(self) -> pd.DataFrame:
        # TODO: not sure if this is a correct/best usage of pvlib
        poa = get_total_irradiance(
            surface_tilt=self.tilt,
            surface_azimuth=self.azimuth,
            solar_zenith=self.forecast["apparent_zenith"],
            solar_azimuth=self.forecast["azimuth"],
            dni=self.forecast["DNI"],
            ghi=self.forecast["GHI"],
            dhi=self.forecast["DHI"],
        )
        p_dc = poa["poa_global"] * self.area * self.efficiency  # in W
        p_dc = self.calibration * p_dc

        return p_dc.to_frame()