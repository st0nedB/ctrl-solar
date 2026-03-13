from __future__ import annotations

from pathlib import Path

from ctrlsolar.assembly import Runtime, build_runtime
from ctrlsolar.config import load_config


def create_app(config_path: str | Path | None = None) -> Runtime:
    config = load_config(config_path)
    return build_runtime(config)


def run(config_path: str | Path | None = None) -> None:
    app = create_app(config_path)
    app.run()
