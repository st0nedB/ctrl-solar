from __future__ import annotations

from ctrlsolar.assembly.registries import CONTROLLERS
from ctrlsolar.config import Config
from ctrlsolar.io import PropertySensor, SumSensor


def build_controllers(config: Config, batteries: list, inverter, meter, weather):
    controllers = []

    available = SumSensor(
        sensors=[PropertySensor(battery, "empty") for battery in batteries],
        filter=lambda value: True if value == 0 else False,
    )
    sensor_today = SumSensor(
        sensors=[PropertySensor(battery, "todays_production") for battery in batteries],
    )
    panels = [panel for battery in batteries for panel in battery.panels]

    for entry in config.controllers:
        if not entry.enabled:
            continue

        if entry.type == "dc_battery_optimizer":
            if len(batteries) < 2:
                continue
            controller = CONTROLLERS[entry.type](batteries=batteries, **entry.config)
        elif entry.type == "reduce_consumption":
            controller = CONTROLLERS[entry.type](
                inverter=inverter,
                meter=meter,
                available=available,
                **entry.config,
            )
        elif entry.type == "production_forecast":
            controller = CONTROLLERS[entry.type](
                panels=panels,
                weather=weather,
                sensor_today=sensor_today,
                **entry.config,
            )
        else:
            raise KeyError(f"Unknown controller type: {entry.type}")

        controllers.append(controller)

    return controllers
