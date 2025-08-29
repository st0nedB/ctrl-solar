import os
import json
import rootutils

root = rootutils.setup_root(__file__, dotenv=True, pythonpath=True, cwd=False)

from ctrlsolar.io import (
    Mqtt,
    MqttSensor,
    ExponentialSmoothing,
    SumSensor,
    PropertySensor,
)
from ctrlsolar.inverter import Deye2MqttFactory, DeyeSunM160G4
from ctrlsolar.battery import GroBroFactory
from ctrlsolar.controller import (
    ReduceConsumption,
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
    root_logger.setLevel(logging.DEBUG)
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
    meter_smooth = ExponentialSmoothing(
        sensor=meter,
        last_k=10,
    )

    weather = OpenMeteoForecast(
        latitude=float(os.environ["LATITUDE"]),
        longitude=float(os.environ["LONGITUDE"]),
        timezone="Europe/Berlin",
    )

    panels = [
        *[
            Panel(
                tilt=22.5,
                azimuth=90,
                area=1.762 * 1.134,
                efficiency=0.22,
                forecast=weather,
            )
            for _ in range(3)
        ],
        Panel(
            tilt=22.5,
            azimuth=180,
            area=1.762 * 1.134,
            efficiency=0.22,
            forecast=weather,
        ),
    ]

    battery_1 = GroBroFactory.initialize(
        mqtt=mqtt,
        serial_number=os.environ["BATTERY1_SN"],
        panels=panels[:2],
        n_batteries_stacked=1,
    )
    battery_2 = GroBroFactory.initialize(
        mqtt=mqtt,
        serial_number=os.environ["BATTERY2_SN"],
        panels=panels[2:],
        n_batteries_stacked=1,
    )
    battery_controller = DCBatteryOptimizer(
        batteries=[battery_1, battery_2],
        full_threshold=95,
        discharge_backoff=100,
        discharge_threshold=800,
    )

    inverter = Deye2MqttFactory.initialize(
        mqtt=mqtt, base_topic="deye", inverter=DeyeSunM160G4
    )
    available = SumSensor(
        sensors=[
            PropertySensor(battery_1, "empty"),
            PropertySensor(battery_2, "empty"),
        ],
        filter=lambda x: True if x == 0 else False,
    )

    power_controller = ReduceConsumption(
        meter=meter_smooth,
        inverter=inverter,
        available=available,
        max_power=800,
        control_threshold=50.0,
    )

    yield_sensor_1 = MqttSensor(
        mqtt=mqtt,
        topic=f"homeassistant/grobro/{os.environ["BATTERY1_SN"].upper()}/state",
        filter=lambda y: (lambda x: 1e3 * float(x) if x is not None else None)(
            json.loads(y)["pv_eng_today"]
        ),
    )
    yield_sensor_2 = MqttSensor(
        mqtt=mqtt,
        topic=f"homeassistant/grobro/{os.environ["BATTERY2_SN"].upper()}/state",
        filter=lambda y: (lambda x: 1e3 * float(x) if x is not None else None)(
            json.loads(y)["pv_eng_today"]
        ),
    )

    sensor_today = SumSensor(sensors=[yield_sensor_1, yield_sensor_2])

    forecast_controller = ProductionForecast(
        panels=panels, weather=weather, sensor_today=sensor_today
    )

    loop = Loop(
        controller=[forecast_controller, battery_controller, power_controller],
        update_interval=30,
    )
    loop.run()


if __name__ == "__main__":
    main()
