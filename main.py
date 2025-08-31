import rootutils
root = rootutils.setup_root(__file__, dotenv=True, pythonpath=True, cwd=False)

import json
from ctrlsolar.io import (
    Mqtt,
    MqttSensor,
    ExponentialSmoothing,
    SumSensor,
    PropertySensor,
)
from ctrlsolar.inverter import *
from ctrlsolar.battery import GroBroFactory
from ctrlsolar.controller import (
    ReduceConsumption,
    ProductionForecast,
    DCBatteryOptimizer,
)
from ctrlsolar.panels import Panel, OpenMeteoForecast
from ctrlsolar.loop import Loop
from ctrlsolar.config import Config
from ctrlsolar.functions import filter_dict_with_keys

import logging
from rich.logging import RichHandler

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(show_time=True, show_level=True, show_path=False)],
)


def main():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    config = Config.from_yaml("/app/config.yaml")

    mqtt = Mqtt(**config.mqtt)
    mqtt.connect()

    weather = OpenMeteoForecast(**config.location)

    meter = MqttSensor(
        mqtt=mqtt,
        topic=config.powermeter["topic"],
        filter=lambda x: filter_dict_with_keys(json.loads(x), **config.powermeter["filter"]),
    )
    if config.powermeter.use_smoothing:
        meter = ExponentialSmoothing(
            sensor=meter,
            last_k=config.loop.update_interval // config.powermeter.update_interval,  # type: ignore
        )

    batteries = []
    for bb in config.batteries:
        cnf = dict(bb)
        panels = [Panel(forecast=weather, **pp) for pp in cnf.pop("panels")]
        cnf.pop("model")
        battery = GroBroFactory.initialize(
            mqtt=mqtt, panels=panels, last_k=config.loop.update_interval // 5, **cnf
        )
        batteries.append(battery)

    battery_controller = DCBatteryOptimizer(
        batteries=batteries,
        **config.loop.battery,
    )

    inverter = Deye2MqttFactory.initialize(
        mqtt=mqtt, topic="deye", inverter=eval(config.inverter.model)
    )
    available = SumSensor(
        sensors=[PropertySensor(bb, "empty") for bb in batteries],
        filter=lambda x: True if x == 0 else False,
    )
    power_controller = ReduceConsumption(
        inverter=inverter, meter=meter, available=available, **config.loop.power
    )

    sensor_today = SumSensor(
        sensors=[PropertySensor(bb, "todays_production") for bb in batteries],
    )

    panels = []
    for bb in config.batteries:
        for pp in bb.panels:
            panels.append(Panel(forecast=weather, **pp))

    forecast_controller = ProductionForecast(
        panels=panels, weather=weather, sensor_today=sensor_today
    )

    loop = Loop(
        controller=[forecast_controller, battery_controller, power_controller],
        update_interval=config.loop.update_interval,
    )
    loop.run()


if __name__ == "__main__":
    main()
