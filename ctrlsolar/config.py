import yaml
from dataclasses import dataclass, field
from ctrlsolar.panels import GenericPanel, PanelGroup
from ctrlsolar.panels.abstract import Panel
import os
from typing import Any

@dataclass
class Config:
    panels: PanelGroup

    latitude: float = 42.46903090913205
    longitude: float = -71.35063628495487
    timezone: str = "America/New_York"

    mqtt_host: str = "homeassistant.local"
    mqtt_port: int = 1883
    mqtt_username: str = field(default_factory=lambda: os.getenv("MQTT_USERNAME", ""))
    mqtt_password: str = field(default_factory=lambda: os.getenv("MQTT_PASSWORD", ""))

    @classmethod
    def from_yaml(cls, file: str):
        config: dict[str, Any] = yaml.safe_load(file) or {}
        panel_list: list[Panel] = []
        for panel in config.get("panels", []):
            panel_list.append(
                GenericPanel(
                    tilt=float(panel["tilt"]),
                    azimuth=float(panel["azimuth"]),
                    area=float(panel["area"]),
                    efficiency=float(panel["efficiency"]),
                    calibration=panel.get("calibration"),
                )
            )

        panels = PanelGroup(panel_list)

        return cls(
            panels=panels,
            latitude=float(config.get("latitude", cls.latitude)),
            longitude=float(config.get("longitude", cls.longitude)),
            timezone=str(config.get("timezone", cls.timezone)),
            mqtt_host=str(config.get("host", cls.mqtt_host)),
            mqtt_port=int(config.get("port", cls.mqtt_port)),
        )