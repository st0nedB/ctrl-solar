from ctrlsolar.mqtt.mqtt import set_mqtt, Mqtt
import ctrlsolar.mqtt.topics as mqtt_topics
from ctrlsolar.controller import EnergyController
from ctrlsolar.battery import Noah2000
from ctrlsolar.panels import OpenMeteoWeather, GenericPanel, PanelGroup
from ctrlsolar.localization import set_timezone
from ctrlsolar.config import Config
from ctrlsolar.history import HistoryStore
from ctrlsolar.web import DashboardServer
import time
import logging

logger = logging.getLogger(__name__)


def publish_ha_autodiscovery(mqtt: Mqtt, device_id: str) -> None:
    mqtt.publish(mqtt_topics.TOPICS["availability"].format(device_id=device_id), "online", retain=True)
    for topic, payload in mqtt_topics.discovery_items(device_id):
        mqtt.publish(topic, payload, retain=True)

def run(config_file: str) -> None:
    config = Config.from_yaml(config_file)
    set_timezone(config.timezone)

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

    # optional: create sensor for energy measurements
    energy_sensor = None
    if config.energy_sensor is not None:
        energy_sensor = config.energy_sensor["type"](config.energy_sensor["topic"])      

    # TODO: For calibration, add later
    # power_sensor = None
    # if config.power_sensor is not None:
    #     power_sensor = config.power_sensor["type"](config.power_sensor["topic"])

    # create the controllers
    controllers = [
        EnergyController(
            battery=battery,
            weather=weather,
            panels=panels,
            p_min=config.power_min,
            p_max=config.power_max,
            energy_sensor=energy_sensor
        )
    ]
    history = None
    if config.history_enabled or config.calibration_enabled:
        history = HistoryStore(config.history_path)
        if config.calibration_apply:
            factors = history.calibration().get("factors")
            if factors is not None:
                controllers[0].set_calibration(factors)

    dashboard = None
    if config.dashboard_enabled:
        dashboard = DashboardServer(
            controller=controllers[0],
            host=config.dashboard_host,
            port=config.dashboard_port,
            history_store=history,
        )
        dashboard.start()

    if config.ha_autodiscovery:
        publish_ha_autodiscovery(mqtt, battery.serial_number)    

    # run in loop
    try:
        last_sample_at = 0.0
        last_calibration_day = None
        time.sleep(30)
        while True:
            for cc in controllers:
                print()
                info = f"Update started for {cc.name}."
                logger.info(info)
                logger.info(len(info) * "-")
                cc.update()
                now = time.monotonic()
                snapshot = None
                sample_interval = config.history_sample_interval_s or config.update_interval_s
                if history is not None and now - last_sample_at >= sample_interval:
                    snapshot = cc.snapshot()
                    history.insert_snapshot(snapshot)
                    last_sample_at = now
                if config.calibration_enabled and history is not None:
                    snapshot = snapshot or cc.snapshot()
                    today = snapshot["timestamp"][:10]
                else:
                    today = None
                if today is not None and today != last_calibration_day:
                    factors = history.learn_calibration(
                        minimum_days=config.calibration_minimum_days,
                        factor_min=config.calibration_factor_min,
                        factor_max=config.calibration_factor_max,
                    )
                    if factors is not None and config.calibration_apply:
                        cc.set_calibration(factors)
                    last_calibration_day = today

            time.sleep(config.update_interval_s)

    except KeyboardInterrupt:
        pass
    finally:
        if dashboard is not None:
            dashboard.stop()
        mqtt.disconnect()

    return

if __name__ == "__main__":
    from ctrlsolar.cli import main

    raise SystemExit(main())
