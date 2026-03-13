from __future__ import annotations

from ctrlsolar.assembly.registries import BATTERY_FACTORIES
from ctrlsolar.config import BatteryConfig, LocationConfig
from ctrlsolar.io import Mqtt
from ctrlsolar.panels import OpenMeteoForecast, Panel


def build_batteries(
    batteries: list[BatteryConfig],
    mqtt: Mqtt,
    site: LocationConfig,
    loop_interval: int,
) -> tuple[list, OpenMeteoForecast]:
    weather = OpenMeteoForecast(
        latitude=site.latitude,
        longitude=site.longitude,
        timezone=site.timezone,
    )

    instances = []
    for config in batteries:
        factory = BATTERY_FACTORIES[config.type]
        panels = [
            Panel(
                forecast=weather,
                tilt=panel.tilt,
                azimuth=panel.azimuth,
                area=panel.area,
                efficiency=panel.efficiency,
                calibration=panel.calibration,
            )
            for panel in config.panels
        ]
        instance = factory(
            mqtt=mqtt,
            serial=config.serial,
            panels=panels,
            n_batteries_stacked=config.stack_count,
            use_smoothing=config.use_smoothing,
            last_k=max(1, loop_interval // 5),
        )
        instances.append(instance)
    return instances, weather
