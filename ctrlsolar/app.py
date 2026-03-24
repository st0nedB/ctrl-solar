from __future__ import annotations
import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig
from ctrlsolar.io.mqtt import set_mqtt

@hydra.main(version_base=None, config_path=".", config_name="defaults")
def run(config: DictConfig) -> None:
    mqtt = instantiate(config.mqtt)
    mqtt.connect()
    set_mqtt(mqtt)
    
    loop = instantiate(config.loop)
    loop.run()

    return

if __name__ == "__main__":
    run()