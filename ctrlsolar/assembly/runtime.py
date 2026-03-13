from __future__ import annotations

from dataclasses import dataclass

from ctrlsolar.assembly.batteries import build_batteries
from ctrlsolar.assembly.controllers import build_controllers
from ctrlsolar.assembly.inverters import build_inverter
from ctrlsolar.assembly.sensors import build_powermeter_sensor
from ctrlsolar.config import Config
from ctrlsolar.io import Mqtt
from ctrlsolar.loop import Loop


@dataclass
class Runtime:
    config: Config
    mqtt: Mqtt
    weather: object
    meter: object
    batteries: list
    inverter: object
    controllers: list
    loop: Loop

    def run(self) -> None:
        self.mqtt.connect()
        self.loop.run()


def build_runtime(config: Config) -> Runtime:
    mqtt = Mqtt(**config.mqtt)
    batteries, weather = build_batteries(
        batteries=config.batteries,
        mqtt=mqtt,
        site=config.site,
        loop_interval=config.loop.update_interval,
    )
    meter = build_powermeter_sensor(
        config=config.powermeter,
        mqtt=mqtt,
        loop_interval=config.loop.update_interval,
    )
    inverter = build_inverter(config.inverter, mqtt)
    controllers = build_controllers(config, batteries, inverter, meter, weather)
    loop = Loop(controller=controllers, update_interval=config.loop.update_interval)
    return Runtime(
        config=config,
        mqtt=mqtt,
        weather=weather,
        meter=meter,
        batteries=batteries,
        inverter=inverter,
        controllers=controllers,
        loop=loop,
    )
