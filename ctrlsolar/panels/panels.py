from pvlib.irradiance import get_total_irradiance   # type:ignore
from ctrlsolar.panels.abstract import Panel, Weather
import numpy as np
import logging
from typing import Optional, Sequence

logger = logging.getLogger(__name__)

class GenericPanel(Panel):
    def __init__(
        self,
        area: float,
        efficiency: float,
        tilt: float,
        azimuth: float,
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
        self.calibration = calibration if calibration is not None else 24 * [1]

    def set_calibration(self, factors: list[float]) -> None:
        if len(factors) != 24:
            raise ValueError("Calibration requires 24 hourly factors.")
        self.calibration = factors

    def predicted_production_by_hour(self, weather: Weather, calibrated: bool = True) -> dict[int, float]:
        weather_today = weather.get()
        poa = get_total_irradiance( # type: ignore
            surface_tilt=self.tilt,
            surface_azimuth=self.azimuth,
            solar_zenith=weather_today["apparent_zenith"],
            solar_azimuth=weather_today["azimuth"],
            dni=weather_today["DNI"],
            ghi=weather_today["GHI"],
            dhi=weather_today["DHI"],
        )
        energy = poa["poa_global"] * self.area * self.efficiency    # type: ignore # in Wh
        if calibrated:
            energy = energy * self.calibration                      # type: ignore
        energy = [float(x) for x in energy.tolist()]                # type: ignore
        energy_by_hour = dict(zip(range(24), energy))

        return energy_by_hour
    
class PanelGroup(Panel):
    def __init__(self, panels: Sequence[Panel,]):
        self._panels = panels

    def set_calibration(self, factors: list[float]) -> None:
        for panel in self._panels:
            if hasattr(panel, "set_calibration"):
                panel.set_calibration(factors)

    def predicted_production_by_hour(self, weather: Weather, calibrated: bool = True) -> dict[int, float]:
        energy = [
            list(x.predicted_production_by_hour(weather, calibrated=calibrated).values())
            for x in self._panels
        ]
        energy = np.sum(np.column_stack(energy), axis=-1, keepdims=False).tolist()
        energy_by_hour = dict(zip(range(24), energy))

        return energy_by_hour
