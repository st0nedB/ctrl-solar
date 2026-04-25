from ctrlsolar.mqtt.mqtt import set_mqtt
from ctrlsolar.controller import EnergyController
from ctrlsolar.battery import Noah2000
import time
from os import PathLike

def run(config: PathLike) -> None:
    mqtt = ...
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
    battery = Noah2000.from_grobro(config.grobro)
    forecast = 

    # create the controllers
    controllers = [
        EnergyController(
            battery=,

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

            time.sleep(self.update_interval)

    except KeyboardInterrupt:
        pass

    return

if __name__ == "__main__":
    run()