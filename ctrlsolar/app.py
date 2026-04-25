from ctrlsolar.mqtt.mqtt import set_mqtt, Mqtt
from ctrlsolar.controller import EnergyController
from ctrlsolar.battery import Noah2000
from ctrlsolar.panels import OpenMeteoWeather, GenericPanel, PanelGroup
from ctrlsolar.config import Config
import time
import logging

logger = logging.getLogger(__name__)

def run(config: Config) -> None:
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

    # create 
    panel_list = [
        GenericPanel(
            tilt=float(panel["tilt"]),
            azimuth=float(panel["azimuth"]),
            area=float(panel["area"]),
            efficiency=float(panel["efficiency"]),
            calibration=panel.get("calibration"),
        ) for panel in config.panels]

    panels = PanelGroup(panel_list)
    battery = Noah2000.from_grobro(config.grobro_root_topic)
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

    # run in loop
    try:
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
    config = Config.from_yaml("config.yaml")
    run(config=config)