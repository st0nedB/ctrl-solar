from dataclasses import dataclass
from collections.abc import Mapping
from typing import Optional
from os import PathLike
import yaml
import os


def env_constructor(loader, node):
    """Constructor for !env tag to load environment variables"""
    env_var = loader.construct_scalar(node)
    env_value = os.getenv(env_var)
    if env_value is None:
        raise ValueError(f"Environment variable '{env_var}' is not set")

    return env_value


# Register the constructor
yaml.add_constructor("!env", env_constructor, yaml.SafeLoader)


@dataclass
class _Config(Mapping):
    def __getitem__(self, key):
        if key in self.__dataclass_fields__:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self):
        return iter(self.__dataclass_fields__)

    def __len__(self):
        return len(self.__dataclass_fields__)


@dataclass
class MqttConfig(_Config):
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None

    def __post_init__(self):
        setattr(self, "port", int(self.port))


@dataclass
class LocationConfig(_Config):
    latitude: float
    longitude: float
    timezone: str

    def __post_init__(self):
        setattr(self, "latitude", float(self.latitude))
        setattr(self, "longitude", float(self.longitude))


@dataclass
class PanelConfig(_Config):
    tilt: float | int
    azimuth: float | int
    area: float | int
    efficiency: float | int


@dataclass
class BatteryConfig(_Config):
    model: str
    serial: str
    panels: list[dict]
    n_batteries_stacked: int
    use_smoothing: bool

    def __post_init__(self):
        panels = [PanelConfig(**cc) for cc in self.panels]
        setattr(self, "panels", panels)


@dataclass
class FilterConfig(_Config):
    dkeys: list[str,]
    dtype: str | float | int
    scale: float


@dataclass
class SensorConfig(_Config):
    topic: str
    filter: FilterConfig
    use_smoothing: Optional[bool] = None
    update_interval: Optional[int] = None


@dataclass
class InverterConfig(_Config):
    topic: str
    model: str


@dataclass
class LoopConfig(_Config):
    update_interval: int
    power: dict
    battery: dict


@dataclass
class Config(_Config):
    mqtt: MqttConfig
    location: LocationConfig
    batteries: list[BatteryConfig]
    powermeter: SensorConfig
    inverter: InverterConfig
    loop: LoopConfig

    @classmethod
    def from_yaml(cls, fn: str | PathLike):
        with open(fn, "r") as file:
            cnf = yaml.safe_load(file)

        return cls(
            mqtt=MqttConfig(**cnf["mqtt"]),
            location=LocationConfig(**cnf["location"]),
            batteries=[BatteryConfig(**cc) for cc in cnf["batteries"]],
            powermeter=SensorConfig(**cnf["powermeter"]),
            inverter=InverterConfig(**cnf["inverter"]),
            loop=LoopConfig(**cnf["loop"]),
        )
