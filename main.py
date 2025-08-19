import os
import json
import rootutils

root = rootutils.setup_root(__file__, dotenv=True, pythonpath=True, cwd=False)

from ctrlsolar.io import Mqtt, MqttConsumer, MqttSensor
from ctrlsolar.inverter import DeyeSunM160G4
from ctrlsolar.battery import Noah2000
from ctrlsolar.controller import ZeroConsumptionController
from ctrlsolar.controller.forecast import ProductionForecast
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

    battery_1 = 

    inverter = DeyeSunM160G4(
        power_sensor=MqttSensor(
            mqtt=mqtt,
            topic="deye/ac/active_power",
            filter=lambda x: float(x) if x is not None else None,
        ),
        production_limit_sensor=MqttSensor(
            mqtt=mqtt,
            topic="deye/settings/active_power_regulation",
            filter=lambda x: float(x) if x is not None else None,
        ),
        production_limit_consumer=MqttConsumer(
            mqtt=mqtt, topic="deye/settings/active_power_regulation/command"
        ),
    )

    controller = ZeroConsumptionController(
        meter=meter,
        inverter=inverter,
        battery=battery,
        max_power=800,
        control_threshold=30.0,
        last_k=3,
    )

    weather=OpenMeteoForecast(
        latitude=47.833301,
        longitude=12.977702,
        timezone="Europe/Berlin",
    )
    panels=[
        *[Panel(
            tilt=67.5,
            azimuth=90,
            area=1.762 * 1.134,
            efficiency=0.22,
            forecast=weather,
        ) for _ in range(3)],
        Panel(
            tilt=67.5,
            azimuth=180,
            area=1.762 * 1.134,
            efficiency=0.22,
            forecast=weather,
        ),
    ]
    sensor_today=MqttSensor(
        mqtt=mqtt,
        topic="noah-2000-battery/0PVPH6ZR23QT00D9",
        filter=lambda y: (lambda x: 1e3 * float(x) if x is not None else None)(
            json.loads(y)["generation_today_kwh"]
        ),
    )

    loop = Loop(controller=[controller, forecast], update_interval=30)
    loop.run()


if __name__ == "__main__":
    main()
