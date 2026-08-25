from datetime import date, timedelta
import tempfile
import unittest

from ctrlsolar.history import HistoryStore


class HistoryStoreTests(unittest.TestCase):
    def test_stores_snapshot_forecast_and_actuals(self):
        with tempfile.TemporaryDirectory() as directory:
            store = HistoryStore(f"{directory}/history.sqlite")
            today = date.today().isoformat()

            store.insert_snapshot(snapshot(today, hour=12, forecast_wh=100, actual_wh=80))

            day = store.day(today)
            live = store.live()
            history = store.range(days=1)

        self.assertEqual(len(live["samples"]), 1)
        self.assertEqual(day["forecast"][12]["predicted_wh"], 100)
        self.assertAlmostEqual(day["forecast"][12]["calibrated_wh"], 110)
        self.assertEqual(day["solar_hourly_wh"][12], 80)
        self.assertAlmostEqual(history["days"][0]["forecast_wh"], 2640)
        self.assertEqual(history["days"][0]["actual_wh"], 80)

    def test_learns_hourly_calibration_from_valid_days(self):
        with tempfile.TemporaryDirectory() as directory:
            store = HistoryStore(f"{directory}/history.sqlite")
            start = date.today() - timedelta(days=6)
            for offset in range(7):
                day = (start + timedelta(days=offset)).isoformat()
                store.insert_snapshot(snapshot(day, hour=12, forecast_wh=100, actual_wh=150))

            factors = store.learn_calibration(minimum_days=7, factor_min=0.5, factor_max=2.0)
            status = store.calibration()

        self.assertIsNotNone(factors)
        self.assertEqual(factors[12], 1.5)
        self.assertEqual(factors[11], 1.0)
        self.assertEqual(status["status"], "learned")
        self.assertEqual(status["valid_day_count"], 7)

    def test_calibration_waits_for_enough_days(self):
        with tempfile.TemporaryDirectory() as directory:
            store = HistoryStore(f"{directory}/history.sqlite")
            store.insert_snapshot(snapshot(date.today().isoformat(), hour=12))

            factors = store.learn_calibration(minimum_days=2)
            status = store.calibration()

        self.assertIsNone(factors)
        self.assertEqual(status["status"], "insufficient_data")
        self.assertEqual(status["valid_day_count"], 1)


def snapshot(day: str, hour: int, forecast_wh: float = 100, actual_wh: float = 90):
    return {
        "timestamp": f"{day}T{hour:02d}:00:00",
        "controller": {
            "phase": "production",
            "last_target_power_w": 200,
            "last_error": None,
        },
        "battery": {
            "serial_number": "BAT001",
            "online": True,
            "state_of_charge": 0.5,
            "output_power_w": 100,
            "panel_power_w": 120,
            "energy_charged_wh": 500,
            "energy_missing_wh": 500,
            "capacity_wh": 1000,
            "energy_out_wh": 20,
        },
        "forecast": {
            "hour": hour,
            "raw_hourly_wh": [forecast_wh] * 24,
            "hourly_wh": [forecast_wh * 1.1] * 24,
        },
        "actuals": {
            "solar_hourly_wh": {hour: actual_wh},
            "ac_hourly_wh": {hour: actual_wh / 2},
        },
    }


if __name__ == "__main__":
    unittest.main()
