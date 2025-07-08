import os
import json
import rootutils

root = rootutils.setup_root(__file__, dotenv=True, pythonpath=True, cwd=False)

from ctrlsolar.io import Mqtt, MqttConsumer, MqttSensor
from ctrlsolar.inverter import DeyeSunM160G4
from ctrlsolar.battery import Noah2000
from ctrlsolar.controller import ZeroConsumptionController
from ctrlsolar.loop import Loop

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
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

    battery = Noah2000(
        state_of_charge_sensor=MqttSensor(
            mqtt=mqtt,
            topic="noah-2000-battery/0PVPH6ZR23QT00D9",
            filter=lambda y: (lambda x: float(x) if x is not None else 0)(
                json.loads(y)["soc"]
            ),
        ),
        mode_sensor=MqttSensor(
            mqtt=mqtt,
            topic="noah-2000-battery/0PVPH6ZR23QT00D9",
            filter=lambda y: (json.loads(y)["work_mode"]),
        ),
        output_power_sensor=MqttSensor(
            mqtt=mqtt,
            topic="noah-2000-battery/0PVPH6ZR23QT00D9",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["output_w"]
            ),
        ),
        solar_sensor=MqttSensor(
            mqtt=mqtt,
            topic="noah-2000-battery/0PVPH6ZR23QT00D9",
            filter=lambda y: (lambda x: float(x) if x is not None else None)(
                json.loads(y)["solar_w"]
            ),
        ),
        n_batteries=2,
    )

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

    loop = Loop(controller=controller, update_interval=60)
    loop.run()


if __name__ == "__main__":
    main()
