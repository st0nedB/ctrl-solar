from __future__ import annotations
from dataclasses import dataclass
import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig
from ctrlsolar.abstracts import Forecast, Sensor, Inverter, Controller
from ctrlsolar.io import Mqtt
from ctrlsolar.loop import Loop

@dataclass
class Runtime:
    mqtt: Mqtt
    forecast: type[Forecast]
    meter: type[Sensor]
    inverter: type[Inverter]
    controllers: list[type[Controller]]
    loop: Loop

    def run(self) -> None:
        self.mqtt.connect()
        self.loop.run()


@hydra.main(version_base=None, config_path=".", config_name="defaults")
def run(config: DictConfig) -> None:
    mqtt = instantiate(config.mqtt)
    forecast = instantiate(config.forecast)
    panels = [factory(forecast=forecast) for factory in instantiate(config.panels)]
    meter = instantiate(config.powermeter, sensor=instantiate(config.powermeter.sensor)(mqtt))

    if config.batteries is not None: 
        batteries = [x(mqtt) for x in instantiate(config.batteries)]
    
    inverter = instantiate(config.inverter)(mqtt=mqtt, )

    return

if __name__ == "__main__":
    run()