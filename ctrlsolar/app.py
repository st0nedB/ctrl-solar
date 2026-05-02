from ctrlsolar.mqtt.mqtt import set_mqtt, Mqtt
import ctrlsolar.mqtt.topics as mqtt_topics
from ctrlsolar.controller import EnergyController
from ctrlsolar.battery import Noah2000
from ctrlsolar.panels import OpenMeteoWeather, GenericPanel, PanelGroup
from ctrlsolar.config import Config
import time
import logging
import argparse

logger = logging.getLogger(__name__)


def publish_ha_autodiscovery(mqtt: Mqtt, device_id: str) -> None:
    mqtt.publish(mqtt_topics.TOPICS["availability"].format(device_id=device_id), "online", retain=True)
    for topic, payload in mqtt_topics.discovery_items(device_id):
        mqtt.publish(topic, payload, retain=True)

def run(config_file: str) -> None:
    config = Config.from_yaml(config_file)

    mqtt = Mqtt(
        host=config.mqtt_host, 
        port=config.mqtt_port,
        password=config.mqtt_password,
        username=config.mqtt_username,
    )
    mqtt.connect()
    set_mqtt(mqtt)

    # add a connection check with timeout and error raising if conenction fails
    for ii in range(5):
        time.sleep(2)
        if mqtt.client.is_connected():
            break

        if ii == 4:
            raise RuntimeError(f"Connection to MQTT broker could not be established.")

    # create solar panels
    panel_list = [
        GenericPanel(
            tilt=float(panel["tilt"]),
            azimuth=float(panel["azimuth"]),
            area=float(panel["area"]),
            efficiency=float(panel["efficiency"]),
            calibration=panel.get("calibration"),
        ) for panel in config.panels]

    panels = PanelGroup(panel_list)
    battery = Noah2000.from_grobro(config.battery_sn)
    weather = OpenMeteoWeather(
        latitude=config.latitude,
        longitude=config.longitude,
        timezone=config.timezone
    )

    # create the controllers
    controllers = [
        EnergyController(
            battery=battery,
            weather=weather,
            panels=panels,
            p_min=config.power_min,
            p_max=config.power_max,
        )
    ]

    if config.ha_autodiscovery:
        publish_ha_autodiscovery(mqtt, battery.serial_number)    

    # run in loop
    try:
        time.sleep(30)
        while True:
            for cc in controllers:
                print()
                info = f"Update started for {cc.name}."
                logger.info(info)
                logger.info(len(info) * "-")
                cc.update()

            time.sleep(config.update_interval_s)

    except KeyboardInterrupt:
        pass

    return

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Run the ctrlsolar app")
    parser.add_argument(
        "--config-file",
        default="example/config.yaml",
        help="Path to YAML config file",
    )
    args = parser.parse_args()
    run(config_file=args.config_file)