from dataclasses import dataclass, field
from ctrlsolar.mqtt.mqtt import MqttSensor
from ctrlsolar.mqtt.library import MAPPINGS
import os
import yaml
from typing import Any, Optional, Type, cast

@dataclass
class Config:
    panels: list[dict[str, Any]]
    battery_sn: str
    power_min: int = 200
    power_max: int = 800
    power_check_topic: Optional[str] = None

    latitude: float = 42.46903090913205
    longitude: float = -71.35063628495487
    timezone: str = "America/New_York"

    mqtt_host: str = "homeassistant.local"
    mqtt_port: int = 1883
    mqtt_username: str = field(default_factory=lambda: os.getenv("MQTT_USERNAME", ""))
    mqtt_password: str = field(default_factory=lambda: os.getenv("MQTT_PASSWORD", ""))

    update_interval_s: int = 300
    ha_autodiscovery: bool = False

    energy_sensor: Optional[dict[str, Any]] = None
    power_sensor: Optional[dict[str, Any]] = None

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, "r", encoding="utf-8") as file:
            config: dict[str, Any] = yaml.safe_load(file) or {}
            
        raw_panels = config.get("panels", [])
        if not isinstance(raw_panels, list):
            raise ValueError("Expected 'panels' to be a list of dictionaries.")
        
        typed_raw_panels = cast(list[Any], raw_panels)
        if not all(isinstance(panel, dict) for panel in typed_raw_panels):
            raise ValueError("Each item in 'panels' must be a dictionary.")

        panels = cast(list[dict[str, Any]], typed_raw_panels)

        # load optionals
        optional = cast(dict[str, Any], config.get("optional") or {})
        energy_sensor = optional.get("energy_sensor", None)
        if energy_sensor is not None:
            energy_sensor["type"] = MAPPINGS[energy_sensor["type"]]
        
        power_sensor = optional.get("power_sensor", None)
        if power_sensor is not None:
            power_sensor["type"] = MAPPINGS[power_sensor["type"]]

        return cls(
            panels=panels,
            battery_sn=str(config.get("battery_sn")),
            power_min=int(config.get("power_min", cls.power_min)),
            power_max=int(config.get("power_max", cls.power_max)),
            latitude=float(config.get("latitude", cls.latitude)),
            longitude=float(config.get("longitude", cls.longitude)),
            timezone=str(config.get("timezone", cls.timezone)),
            mqtt_host=str(config.get("host", cls.mqtt_host)),
            mqtt_port=int(config.get("port", cls.mqtt_port)),
            update_interval_s=int(config.get("update_interval_s", cls.update_interval_s)), 
            ha_autodiscovery=bool(config.get("ha_autodiscovery", cls.ha_autodiscovery)),
            energy_sensor=energy_sensor,
            power_sensor=power_sensor
        )