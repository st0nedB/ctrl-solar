from ctrlsolar.panels.abstract import Weather, Panel
from ctrlsolar.controller.abstract import Controller
from ctrlsolar.localization import get_timezone
from ctrlsolar.mqtt.mqtt import get_mqtt
from ctrlsolar.mqtt.topics import (
    HOURLY_FORECAST_ATTRIBUTES_TOPIC_TEMPLATE,
    HOURLY_FORECAST_STATE_TOPIC_TEMPLATE,
)
from datetime import datetime

class EnergyForecast(Controller):
    def __init__(
        self,
        weather: Weather,
        panels: Panel,
        device_id: str,
    ):
        self._weather = weather
        self._panels = panels
        self._device_id = device_id

    def hourly_production_estimates(self) -> list[float,]:
        return list(self._panels.predicted_production_by_hour(self._weather).values())

    def next_hour_production_estimate(self) -> float:
        hour = datetime.now(get_timezone()).hour
        return self._panels.predicted_production_by_hour(self._weather)[hour]

    def daily_production_estimate(self) -> float:
        p_dcs = sum(self.hourly_production_estimates())
        return p_dcs

    def remaining_energy_production_today(self, remaining_hours: int) -> float:
        hour = datetime.now(get_timezone()).hour
        energy = sum(self.hourly_production_estimates()[hour : hour + remaining_hours])
        return energy

    def remaining_production_hours_today(self, cutoff_energy_kWh: float) -> int:
        hour = datetime.now(get_timezone()).hour
        energy = self.hourly_production_estimates()[hour:]
        index = [x < cutoff_energy_kWh for x in energy].index(True)
        return index

    def _publish(self):
        mqtt = get_mqtt()
        energy = {
            hour: round(value, 2)
            for hour, value in enumerate(self.hourly_production_estimates())
        }
        mqtt.publish(
            HOURLY_FORECAST_STATE_TOPIC_TEMPLATE.format(device_id=self._device_id),
            datetime.now(get_timezone()).date().isoformat(),
        )
        mqtt.publish(
            HOURLY_FORECAST_ATTRIBUTES_TOPIC_TEMPLATE.format(device_id=self._device_id),
            energy,
        )
        return
    
    def update(self):
        _ = self.hourly_production_estimates()
        self._publish()
        return