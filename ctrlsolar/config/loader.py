from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from ctrlsolar.config.models import Config


DEFAULT_CONFIG_PATH = Path(__file__).with_name("defaults.yaml")
ENV_PREFIX = "CTRLSOLAR__"


def load_config(path: str | os.PathLike[str] | None = None) -> Config:
    data = load_raw_config(path)
    return Config.from_dict(data)


def load_raw_config(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    merged = _load_yaml(DEFAULT_CONFIG_PATH)
    if path is not None:
        merged = _deep_merge(merged, _load_yaml(Path(path)))
    _apply_env_overrides(merged)
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config file {path} must contain a mapping at the root.")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        current = result.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            result[key] = _deep_merge(current, value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(data: dict[str, Any]) -> None:
    for key, raw_value in os.environ.items():
        if not key.startswith(ENV_PREFIX):
            continue
        path = key[len(ENV_PREFIX) :].lower().split("__")
        _set_by_path(data, path, yaml.safe_load(raw_value))


def _set_by_path(target: Any, path: list[str], value: Any) -> None:
    current = target
    for index, segment in enumerate(path[:-1]):
        if isinstance(current, list):
            current = current[int(segment)]
            continue
        next_value = current.get(segment)
        if next_value is None:
            next_value = [] if _looks_like_index(path[index + 1]) else {}
            current[segment] = next_value
        current = next_value

    leaf = path[-1]
    if isinstance(current, list):
        current[int(leaf)] = value
    else:
        current[leaf] = value


def _looks_like_index(value: str) -> bool:
    return value.isdigit()
