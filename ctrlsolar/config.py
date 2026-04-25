import yaml
from dataclasses import dataclass, field
import os
from typing import Any, Optional, cast

@dataclass
class Config:
    panels: list[dict[str, Any]]
    power_min: int = 200
    power_max: int = 800
    power_check_topic: Optional[str] = None
    grobro_root_topic: str = "homeassistant/grobro"

    latitude: float = 42.46903090913205
    longitude: float = -71.35063628495487
    timezone: str = "America/New_York"

    mqtt_host: str = "homeassistant.local"
    mqtt_port: int = 1883
    mqtt_username: str = field(default_factory=lambda: os.getenv("MQTT_USERNAME", ""))
    mqtt_password: str = field(default_factory=lambda: os.getenv("MQTT_PASSWORD", ""))

    update_interval_s: int = 3600

    @classmethod
    def from_yaml(cls, file: str):
        config: dict[str, Any] = yaml.safe_load(file) or {}
        raw_panels = config.get("panels", [])
        if not isinstance(raw_panels, list):
            raise ValueError("Expected 'panels' to be a list of dictionaries.")
        
        typed_raw_panels = cast(list[Any], raw_panels)
        if not all(isinstance(panel, dict) for panel in typed_raw_panels):
            raise ValueError("Each item in 'panels' must be a dictionary.")

        panels = cast(list[dict[str, Any]], typed_raw_panels)

        return cls(
            panels=panels,
            power_min=int(config.get("power_min", cls.power_min)),
            power_max=int(config.get("power_max", cls.power_max)),
            grobro_root_topic=str(config.get("grobro_root_topic", cls.grobro_root_topic)),
            latitude=float(config.get("latitude", cls.latitude)),
            longitude=float(config.get("longitude", cls.longitude)),
            timezone=str(config.get("timezone", cls.timezone)),
            mqtt_host=str(config.get("host", cls.mqtt_host)),
            mqtt_port=int(config.get("port", cls.mqtt_port)),
            update_interval_s=int(config.get("update_interval_s", cls.update_interval_s))
        )