import tempfile
import tomllib
import unittest

import yaml

from ctrlsolar import cli
from ctrlsolar.controller.energy import EnergyController
from ctrlsolar.config import Config
from ctrlsolar.localization import set_timezone
from ctrlsolar.web.routes import ApiError, live_payload, route_api


class FakeController:
    def snapshot(self):
        return {"timestamp": "now", "battery": {"online": True}}


class DashboardTests(unittest.TestCase):
    def test_config_loads_dashboard_settings(self):
        config = {
            "battery_sn": "BAT001",
            "panels": [],
            "dashboard": {"enabled": True, "host": "127.0.0.1", "port": 9000},
            "history": {"enabled": True, "path": "/tmp/history.sqlite", "sample_interval_s": 60},
            "calibration": {"enabled": True, "apply": True, "minimum_days": 3},
        }
        with tempfile.NamedTemporaryFile("w", suffix=".yaml") as file:
            yaml.safe_dump(config, file)
            file.flush()

            loaded = Config.from_yaml(file.name)

        self.assertTrue(loaded.dashboard_enabled)
        self.assertEqual(loaded.dashboard_host, "127.0.0.1")
        self.assertEqual(loaded.dashboard_port, 9000)
        self.assertTrue(loaded.history_enabled)
        self.assertEqual(loaded.history_path, "/tmp/history.sqlite")
        self.assertEqual(loaded.history_sample_interval_s, 60)
        self.assertTrue(loaded.calibration_enabled)
        self.assertTrue(loaded.calibration_apply)
        self.assertEqual(loaded.calibration_minimum_days, 3)

    def test_live_payload_uses_controller_snapshot(self):
        self.assertEqual(
            live_payload(FakeController()),
            {"timestamp": "now", "battery": {"online": True}},
        )

    def test_history_routes_return_empty_payload_when_history_is_disabled(self):
        self.assertEqual(
            route_api("/api/history/range?days=7", FakeController()),
            (200, {"days": []}),
        )

    def test_bad_history_query_raises_api_error(self):
        with self.assertRaises(ApiError):
            route_api("/api/history/day?date=nope", FakeController(), FakeHistory())

    def test_cli_run_accepts_config_argument(self):
        calls = []
        original_run = cli.run
        try:
            cli.run = calls.append
            exit_code = cli.main(["run", "--config", "example/config.yaml"])
        finally:
            cli.run = original_run

        self.assertEqual(exit_code, 0)
        self.assertEqual(calls, ["example/config.yaml"])

    def test_static_files_are_packaged(self):
        with open("pyproject.toml", "rb") as file:
            data = tomllib.load(file)

        self.assertIn(
            "web/static/*",
            data["tool"]["setuptools"]["package-data"]["ctrlsolar"],
        )

    def test_energy_controller_snapshot_tolerates_missing_values(self):
        set_timezone("UTC")
        controller = EnergyController.__new__(EnergyController)
        controller._last_phase = "battery"
        controller._last_target_power = 200
        controller._last_updated_at = "then"
        controller._last_error = None
        controller._battery = BrokenBattery()
        controller._forecast = BrokenSnapshot()
        controller._monitor = BrokenSnapshot()

        snapshot = controller.snapshot()

        self.assertEqual(snapshot["controller"]["phase"], "battery")
        self.assertIsNone(snapshot["battery"]["online"])
        self.assertIsNone(snapshot["forecast"])
        self.assertIsNone(snapshot["actuals"])


class BrokenBattery:
    serial_number = "BAT001"

    def __getattr__(self, name):
        raise RuntimeError(name)


class BrokenSnapshot:
    def snapshot(self):
        raise RuntimeError("broken")


class FakeHistory:
    def day(self, day):
        return {"date": day}


if __name__ == "__main__":
    unittest.main()
