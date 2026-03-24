from __future__ import annotations
import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig
from ctrlsolar.io.mqtt import set_mqtt
import time

@hydra.main(version_base=None, config_path=".", config_name="defaults")
def run(config: DictConfig) -> None:
    mqtt = instantiate(config.mqtt)
    mqtt.connect()
    set_mqtt(mqtt)

    # add a connection check with timeout and error raising if conenction fails
    for ii in range(5):
        time.sleep(2)
        if mqtt.client.is_connected():
            break

        if ii == 4:
            raise RuntimeError(f"Connection to MQTT broker could not be established.")
        
    
    loop = instantiate(config.loop)
    loop.run()

    return

if __name__ == "__main__":
    run()