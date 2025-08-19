import os
import json
import rootutils

root = rootutils.setup_root(__file__, dotenv=True, pythonpath=True, cwd=False)

from ctrlsolar.io import Mqtt, MqttSensor
from ctrlsolar.inverter import Deye2MqttFactory, DeyeSunM160G4
from ctrlsolar.battery import NoahMqttFactory
from ctrlsolar.controller import (
    ZeroConsumptionController,
    ProductionForecast,
    DCBatteryOptimizer,
)
from ctrlsolar.panels import Panel, OpenMeteoForecast
from ctrlsolar.loop import Loop

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
    mqtt = Mqtt(
        broker=os.environ["MQTT_URL"],
        port=int(os.environ["MQTT_PORT"]),
        username=os.environ["MQTT_USER"],
        password=os.environ["MQTT_PASSWD"],
    )
    mqtt.connect()

    meter = MqttSensor(
        mqtt=mqtt,
        topic="tele/esp_pwr_mtr/SENSOR",
        filter=lambda y: (lambda x: float(x) if x is not None else None)(
            json.loads(y)["ENERGY"]["Power"]
        ),
    )

    weather = OpenMeteoForecast(
        latitude=47.833301,
        longitude=12.977702,
        timezone="Europe/Berlin",
    )

    panels = [
        *[
            Panel(
                tilt=67.5,
                azimuth=90,
                area=1.762 * 1.134,
                efficiency=0.22,
                forecast=weather,
            )
            for _ in range(3)
        ],
        Panel(
            tilt=67.5,
            azimuth=180,
            area=1.762 * 1.134,
            efficiency=0.22,
            forecast=weather,
        ),
    ]

    battery_1 = NoahMqttFactory.initialize(
        mqtt=mqtt,
        base_topic="noah-2000-battery/0PVPH6ZR23QT00D9",
        panels=panels[:2],
        n_batteries_stacked=1,
    )
    battery_2 = NoahMqttFactory.initialize(
        mqtt=mqtt,
        base_topic="noah-2000-battery/0PVPH6ZR23QT019U",
        panels=panels[2:],
        n_batteries_stacked=1,
    )
    battery_controller = DCBatteryOptimizer(
        batteries=[battery_1, battery_2],
        full_threshold=0.95,
        discharge_backoff=100,
        discharge_threshold=200,
    )

    inverter = Deye2MqttFactory.initialize(
        mqtt=mqtt, base_topic="deye", inverter=DeyeSunM160G4
    )
    power_controller = ZeroConsumptionController(
        meter=meter,
        inverter=inverter,
        max_power=800,
        control_threshold=100.0,
        last_k=3,
    )

    sensor_today = MqttSensor(
        mqtt=mqtt,
        topic="noah-2000-battery/0PVPH6ZR23QT00D9",
        filter=lambda y: (lambda x: 1e3 * float(x) if x is not None else None)(
            json.loads(y)["generation_today_kwh"]
        ),
    )
    forecast = ProductionForecast(panels=panels, weather=weather, sensor_today=sensor_today)

    loop = Loop(controller=[power_controller, battery_controller, forecast], update_interval=30)
    loop.run()


if __name__ == "__main__":
    main()
