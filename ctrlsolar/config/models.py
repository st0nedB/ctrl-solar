from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class _Config(Mapping):
    def __getitem__(self, key: str) -> Any:
        if key in self.__dataclass_fields__:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self):
        return iter(self.__dataclass_fields__)

    def __len__(self) -> int:
        return len(self.__dataclass_fields__)


@dataclass
class MqttConfig(_Config):
    host: str
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None

    def __post_init__(self) -> None:
        self.port = int(self.port)


@dataclass
class LocationConfig(_Config):
    latitude: float
    longitude: float
    timezone: str

    def __post_init__(self) -> None:
        self.latitude = float(self.latitude)
        self.longitude = float(self.longitude)


@dataclass
class PanelConfig(_Config):
    tilt: float
    azimuth: float
    area: float
    efficiency: float
    calibration: Optional[list[float]] = None

    def __post_init__(self) -> None:
        self.tilt = float(self.tilt)
        self.azimuth = float(self.azimuth)
        self.area = float(self.area)
        self.efficiency = float(self.efficiency)


@dataclass
class BatteryConfig(_Config):
    type: str
    serial: str
    panels: list[PanelConfig]
    stack_count: int = 1
    use_smoothing: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BatteryConfig":
        data = dict(raw)
        model = data.pop("model", None)
        if "type" not in data and model is not None:
            data["type"] = model
        stacked = data.pop("n_batteries_stacked", None)
        if "stack_count" not in data and stacked is not None:
            data["stack_count"] = stacked
        panels = [PanelConfig(**panel) for panel in data.pop("panels", [])]
        return cls(panels=panels, **data)

    def __post_init__(self) -> None:
        self.stack_count = int(self.stack_count)
        self.use_smoothing = bool(self.use_smoothing)


@dataclass
class FilterConfig(_Config):
    path: list[str]
    dtype: str
    scale: float = 1.0

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "FilterConfig":
        data = dict(raw)
        dkeys = data.pop("dkeys", None)
        if "path" not in data and dkeys is not None:
            data["path"] = dkeys
        return cls(**data)

    def __post_init__(self) -> None:
        self.scale = float(self.scale)


@dataclass
class SmoothingConfig(_Config):
    kind: str = "exponential"
    source_interval: Optional[int] = None
    last_k: Optional[int] = None

    def __post_init__(self) -> None:
        if self.source_interval is not None:
            self.source_interval = int(self.source_interval)
        if self.last_k is not None:
            self.last_k = int(self.last_k)


@dataclass
class SensorConfig(_Config):
    topic: str
    filter: FilterConfig
    type: str = "mqtt_sensor"
    smoothing: Optional[SmoothingConfig] = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SensorConfig":
        data = dict(raw)
        smoothing = data.get("smoothing")
        if smoothing is None and data.pop("use_smoothing", False):
            smoothing = {
                "kind": "exponential",
                "source_interval": data.pop("update_interval", None),
            }
        else:
            data.pop("update_interval", None)
        data["filter"] = FilterConfig.from_dict(data["filter"])
        if smoothing is not None:
            data["smoothing"] = SmoothingConfig(**smoothing)
        return cls(**data)


@dataclass
class InverterConfig(_Config):
    model: str
    transport: str = "deye_mqtt"
    topic_prefix: str = "deye"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "InverterConfig":
        data = dict(raw)
        topic = data.pop("topic", None)
        if "topic_prefix" not in data and topic is not None:
            data["topic_prefix"] = topic
        return cls(**data)


@dataclass
class ControllerConfig(_Config):
    type: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ControllerConfig":
        data = dict(raw)
        controller_type = str(data.pop("type"))
        enabled = bool(data.pop("enabled", True))
        return cls(type=controller_type, enabled=enabled, config=data)


@dataclass
class LoopConfig(_Config):
    update_interval: int = 60

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LoopConfig":
        data = dict(raw)
        data.pop("power", None)
        data.pop("battery", None)
        return cls(**data)

    def __post_init__(self) -> None:
        self.update_interval = int(self.update_interval)


@dataclass
class Config(_Config):
    mqtt: MqttConfig
    site: LocationConfig
    batteries: list[BatteryConfig]
    powermeter: SensorConfig
    inverter: InverterConfig
    controllers: list[ControllerConfig]
    loop: LoopConfig

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Config":
        data = dict(raw)
        if "location" in data:
            legacy_location = data.pop("location")
            merged_site = dict(data.get("site", {}))
            merged_site.update(legacy_location)
            data["site"] = merged_site

        batteries = [BatteryConfig.from_dict(item) for item in data.get("batteries", [])]
        controllers = data.get("controllers")
        if controllers is None:
            controllers = _controllers_from_legacy_shape(data, batteries)

        return cls(
            mqtt=MqttConfig(**data["mqtt"]),
            site=LocationConfig(**data["site"]),
            batteries=batteries,
            powermeter=SensorConfig.from_dict(data["powermeter"]),
            inverter=InverterConfig.from_dict(data["inverter"]),
            controllers=[ControllerConfig.from_dict(item) for item in controllers],
            loop=LoopConfig.from_dict(data["loop"]),
        )


def _controllers_from_legacy_shape(
    data: dict[str, Any], batteries: list[BatteryConfig]
) -> list[dict[str, Any]]:
    loop = data.get("loop", {})
    power = dict(loop.get("power", {}))
    battery = dict(loop.get("battery", {}))

    controllers: list[dict[str, Any]] = []
    if len(batteries) > 1:
        controllers.append(
            {
                "type": "dc_battery_optimizer",
                "enabled": True,
                **battery,
            }
        )

    controllers.append(
        {
            "type": "reduce_consumption",
            "enabled": True,
            **power,
        }
    )
    controllers.append({"type": "production_forecast", "enabled": True})
    return controllers
