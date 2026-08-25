from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
import sqlite3
from statistics import median
from typing import Any


class HistoryStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS samples (
                    timestamp TEXT PRIMARY KEY,
                    local_date TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    serial TEXT,
                    phase TEXT,
                    target_power_w REAL,
                    online INTEGER,
                    soc REAL,
                    output_power_w REAL,
                    panel_power_w REAL,
                    energy_charged_wh REAL,
                    energy_missing_wh REAL,
                    capacity_wh REAL,
                    energy_out_wh REAL,
                    solar_actual_wh REAL,
                    ac_actual_wh REAL,
                    error TEXT
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS forecasts (
                    local_date TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    predicted_wh REAL,
                    calibrated_wh REAL,
                    PRIMARY KEY (local_date, hour)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS calibration_factors (
                    hour INTEGER PRIMARY KEY,
                    factor REAL NOT NULL,
                    learned_at TEXT NOT NULL,
                    valid_day_count INTEGER NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS calibration_runs (
                    learned_at TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    valid_day_count INTEGER NOT NULL,
                    message TEXT
                )
                """
            )

    def insert_snapshot(self, snapshot: dict[str, Any]) -> None:
        timestamp = snapshot["timestamp"]
        dt = datetime.fromisoformat(timestamp)
        battery = snapshot.get("battery") or {}
        controller = snapshot.get("controller") or {}
        actuals = snapshot.get("actuals") or {}
        forecast = snapshot.get("forecast") or {}
        hour = int(forecast.get("hour", dt.hour))
        local_date = dt.date().isoformat()

        with self.connect() as db:
            db.execute(
                """
                INSERT OR REPLACE INTO samples VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    timestamp,
                    local_date,
                    hour,
                    battery.get("serial_number"),
                    controller.get("phase"),
                    controller.get("last_target_power_w"),
                    _bool_int(battery.get("online")),
                    battery.get("state_of_charge"),
                    battery.get("output_power_w"),
                    battery.get("panel_power_w"),
                    battery.get("energy_charged_wh"),
                    battery.get("energy_missing_wh"),
                    battery.get("capacity_wh"),
                    battery.get("energy_out_wh"),
                    _hour_value(actuals.get("solar_hourly_wh"), hour),
                    _hour_value(actuals.get("ac_hourly_wh"), hour),
                    controller.get("last_error"),
                ),
            )
            raw = forecast.get("raw_hourly_wh") or forecast.get("hourly_wh") or []
            calibrated = forecast.get("hourly_wh") or []
            db.executemany(
                "INSERT OR REPLACE INTO forecasts VALUES (?, ?, ?, ?)",
                [
                    (local_date, hour, _list_value(raw, hour), _list_value(calibrated, hour))
                    for hour in range(24)
                ],
            )

    def live(self, limit: int = 96) -> dict[str, Any]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM samples ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return {"samples": [dict(row) for row in reversed(rows)]}

    def day(self, day: str) -> dict[str, Any]:
        _parse_date(day)
        with self.connect() as db:
            samples = db.execute(
                "SELECT * FROM samples WHERE local_date = ? ORDER BY timestamp",
                (day,),
            ).fetchall()
            forecasts = db.execute(
                "SELECT hour, predicted_wh, calibrated_wh FROM forecasts WHERE local_date = ? ORDER BY hour",
                (day,),
            ).fetchall()

        return {
            "date": day,
            "samples": [dict(row) for row in samples],
            "forecast": [dict(row) for row in forecasts],
            "solar_hourly_wh": _hourly_actual(samples, "solar_actual_wh"),
            "ac_hourly_wh": _hourly_actual(samples, "ac_actual_wh"),
        }

    def range(self, days: int = 30) -> dict[str, Any]:
        with self.connect() as db:
            start_day = (date.today() - timedelta(days=max(days, 1) - 1)).isoformat()
            sample_rows = db.execute(
                "SELECT * FROM samples WHERE local_date >= ? ORDER BY local_date",
                (start_day,),
            ).fetchall()
            forecast_rows = db.execute(
                """
                SELECT local_date, SUM(calibrated_wh) AS forecast_wh
                FROM forecasts
                WHERE local_date >= ?
                GROUP BY local_date
                """,
                (start_day,),
            ).fetchall()

        forecast_by_day = {
            row["local_date"]: row["forecast_wh"] for row in forecast_rows
        }
        actual_by_day = _daily_actual(sample_rows, "solar_actual_wh")
        dates = sorted(set(forecast_by_day) | set(actual_by_day))[-days:]
        return {
            "days": [
                _with_error(
                    {
                        "date": day,
                        "forecast_wh": forecast_by_day.get(day),
                        "actual_wh": actual_by_day.get(day),
                    }
                )
                for day in dates
            ]
        }

    def calibration(self) -> dict[str, Any]:
        with self.connect() as db:
            factors = db.execute(
                "SELECT hour, factor, learned_at, valid_day_count FROM calibration_factors ORDER BY hour"
            ).fetchall()
            run = db.execute(
                "SELECT * FROM calibration_runs ORDER BY learned_at DESC LIMIT 1"
            ).fetchone()
        return {
            "factors": [row["factor"] for row in factors] if len(factors) == 24 else None,
            "learned_at": factors[0]["learned_at"] if factors else None,
            "valid_day_count": (
                factors[0]["valid_day_count"]
                if factors
                else run["valid_day_count"] if run else 0
            ),
            "status": run["status"] if run else "not_learned",
            "message": run["message"] if run else None,
        }

    def learn_calibration(
        self,
        minimum_days: int = 7,
        factor_min: float = 0.5,
        factor_max: float = 1.5,
    ) -> list[float] | None:
        rows = self._training_rows()
        valid_days = {row["local_date"] for row in rows}
        learned_at = datetime.now().isoformat(timespec="seconds")
        if len(valid_days) < minimum_days:
            self._save_calibration_run(
                learned_at, "insufficient_data", len(valid_days), f"Need {minimum_days} valid days."
            )
            return None

        ratios = {hour: [] for hour in range(24)}
        for row in rows:
            if row["predicted_wh"] and row["actual_wh"] is not None:
                ratios[row["hour"]].append(row["actual_wh"] / row["predicted_wh"])

        factors = [
            max(factor_min, min(factor_max, median(ratios[hour]) if ratios[hour] else 1.0))
            for hour in range(24)
        ]
        with self.connect() as db:
            db.executemany(
                "INSERT OR REPLACE INTO calibration_factors VALUES (?, ?, ?, ?)",
                [(hour, factors[hour], learned_at, len(valid_days)) for hour in range(24)],
            )
        self._save_calibration_run(learned_at, "learned", len(valid_days), None)
        return factors

    def _training_rows(self) -> list[sqlite3.Row]:
        with self.connect() as db:
            return db.execute(
                """
                SELECT f.local_date, f.hour, f.predicted_wh, MAX(s.solar_actual_wh) AS actual_wh
                FROM forecasts f
                JOIN samples s ON s.local_date = f.local_date AND s.hour = f.hour
                GROUP BY f.local_date, f.hour
                HAVING actual_wh IS NOT NULL
                """
            ).fetchall()

    def _save_calibration_run(
        self, learned_at: str, status: str, valid_day_count: int, message: str | None
    ) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO calibration_runs VALUES (?, ?, ?, ?)",
                (learned_at, status, valid_day_count, message),
            )


def _parse_date(value: str) -> None:
    date.fromisoformat(value)


def _bool_int(value) -> int | None:
    return None if value is None else int(bool(value))


def _list_value(values: list, index: int):
    return values[index] if len(values) > index else None


def _hour_value(values, hour: int):
    if values is None:
        return None
    if isinstance(values, dict):
        return values.get(hour, values.get(str(hour)))
    return _list_value(values, hour)


def _hourly_actual(rows, column: str) -> list[float | None]:
    result = [None] * 24
    for row in rows:
        hour = row["hour"]
        value = row[column]
        if value is not None:
            result[hour] = max(result[hour] or 0, value)
    return result


def _daily_actual(rows, column: str) -> dict[str, float]:
    hourly: dict[str, dict[int, float]] = defaultdict(dict)
    for row in rows:
        if row[column] is not None:
            hourly[row["local_date"]][row["hour"]] = max(
                hourly[row["local_date"]].get(row["hour"], 0), row[column]
            )
    return {day: sum(values.values()) for day, values in hourly.items()}


def _with_error(row: dict[str, Any]) -> dict[str, Any]:
    forecast = row["forecast_wh"]
    actual = row["actual_wh"]
    row["error_wh"] = None if forecast is None or actual is None else actual - forecast
    row["error_percent"] = (
        None
        if forecast in (None, 0) or actual is None
        else 100 * (actual - forecast) / forecast
    )
    return row
