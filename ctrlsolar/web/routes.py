from __future__ import annotations

import json
from datetime import date
from urllib.parse import parse_qs, urlparse


class ApiError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def live_payload(controller) -> dict:
    return controller.snapshot()


def route_api(path: str, controller, history_store=None) -> tuple[int, dict]:
    parsed = urlparse(path)
    params = parse_qs(parsed.query)
    if parsed.path == "/api/live":
        return 200, live_payload(controller)
    if history_store is None:
        return 200, _empty_history(parsed.path)
    if parsed.path == "/api/history/day":
        return 200, history_store.day(_date_param(params, "date"))
    if parsed.path == "/api/history/range":
        return 200, history_store.range(_int_param(params, "days", 30))
    if parsed.path == "/api/calibration":
        return 200, history_store.calibration()
    raise ApiError("Unknown API route.", 404)


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _date_param(params: dict, name: str) -> str:
    value = params.get(name, [None])[0]
    if not value:
        raise ApiError(f"Missing query parameter: {name}")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ApiError(f"Invalid date query parameter: {name}") from exc
    return value


def _int_param(params: dict, name: str, default: int) -> int:
    value = params.get(name, [default])[0]
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ApiError(f"Invalid integer query parameter: {name}") from exc


def _empty_history(path: str) -> dict:
    if path == "/api/history/day":
        return {
            "date": None,
            "samples": [],
            "forecast": [],
            "solar_hourly_wh": [],
            "ac_hourly_wh": [],
            "quality_spans": [],
        }
    if path == "/api/history/range":
        return {"days": []}
    if path == "/api/calibration":
        return {
            "factors": None,
            "status": "disabled",
            "valid_day_count": 0,
            "ignored_invalid_samples": 0,
            "ignored_invalid_days": 0,
        }
    raise ApiError("Unknown API route.", 404)
