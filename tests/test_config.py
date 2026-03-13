import os
import tempfile
import textwrap
import unittest

from ctrlsolar.config import load_config


class ConfigLoaderTests(unittest.TestCase):
    def test_load_config_merges_legacy_shape_and_env_overrides(self):
        config_text = textwrap.dedent(
            """
            mqtt:
              host: broker
              port: 1883
            location:
              latitude: 47.0
              longitude: 12.0
              timezone: Europe/Berlin
            batteries:
              - model: noah2000
                serial: BAT001
                n_batteries_stacked: 2
                use_smoothing: true
                panels:
                  - tilt: 45
                    azimuth: 180
                    area: 2.0
                    efficiency: 0.22
              - model: noah2000
                serial: BAT002
                n_batteries_stacked: 2
                use_smoothing: false
                panels:
                  - tilt: 45
                    azimuth: 180
                    area: 2.0
                    efficiency: 0.22
            powermeter:
              topic: tele/power/SENSOR
              filter:
                dkeys: [ENERGY, Power]
                dtype: float
                scale: 1.0
              use_smoothing: true
              update_interval: 10
            inverter:
              model: DeyeSunM160G4
              topic: deye
            loop:
              update_interval: 60
              power:
                max_power: 600
                min_power: 80
                control_threshold_W: 50
                offset: -10.0
              battery:
                full_threshold: 0.95
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(config_text)

            previous = os.environ.get("CTRLSOLAR__MQTT__HOST")
            os.environ["CTRLSOLAR__MQTT__HOST"] = "env-broker"
            try:
                config = load_config(path)
            finally:
                if previous is None:
                    os.environ.pop("CTRLSOLAR__MQTT__HOST", None)
                else:
                    os.environ["CTRLSOLAR__MQTT__HOST"] = previous

        self.assertEqual(config.mqtt.host, "env-broker")
        self.assertEqual(config.site.timezone, "Europe/Berlin")
        self.assertEqual(config.batteries[0].type, "noah2000")
        self.assertEqual(config.batteries[0].stack_count, 2)
        self.assertEqual(config.powermeter.smoothing.kind, "exponential")
        self.assertEqual(
            [controller.type for controller in config.controllers],
            [
                "dc_battery_optimizer",
                "reduce_consumption",
                "production_forecast",
            ],
        )

    def test_env_override_updates_nested_list_value(self):
        config_text = textwrap.dedent(
            """
            mqtt:
              host: broker
              port: 1883
            site:
              latitude: 47.0
              longitude: 12.0
              timezone: Europe/Berlin
            batteries:
              - type: noah2000
                serial: BAT001
                stack_count: 2
                panels:
                  - tilt: 45
                    azimuth: 180
                    area: 2.0
                    efficiency: 0.22
            powermeter:
              topic: tele/power/SENSOR
              filter:
                path: [ENERGY, Power]
                dtype: float
            inverter:
              model: DeyeSunM160G4
            controllers:
              - type: reduce_consumption
            loop:
              update_interval: 60
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(config_text)

            previous = os.environ.get("CTRLSOLAR__BATTERIES__0__SERIAL")
            os.environ["CTRLSOLAR__BATTERIES__0__SERIAL"] = "BAT999"
            try:
                config = load_config(path)
            finally:
                if previous is None:
                    os.environ.pop("CTRLSOLAR__BATTERIES__0__SERIAL", None)
                else:
                    os.environ["CTRLSOLAR__BATTERIES__0__SERIAL"] = previous

        self.assertEqual(config.batteries[0].serial, "BAT999")

    def test_env_override_updates_site_position(self):
        config_text = textwrap.dedent(
            """
            mqtt:
              host: broker
              port: 1883
            site:
              latitude: 0.0
              longitude: 0.0
              timezone: UTC
            batteries: []
            powermeter:
              topic: tele/power/SENSOR
              filter:
                path: [ENERGY, Power]
                dtype: float
            inverter:
              model: DeyeSunM160G4
            controllers:
              - type: reduce_consumption
            loop:
              update_interval: 60
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(config_text)

            previous_lat = os.environ.get("CTRLSOLAR__SITE__LATITUDE")
            previous_lon = os.environ.get("CTRLSOLAR__SITE__LONGITUDE")
            previous_tz = os.environ.get("CTRLSOLAR__SITE__TIMEZONE")
            os.environ["CTRLSOLAR__SITE__LATITUDE"] = "47.1234"
            os.environ["CTRLSOLAR__SITE__LONGITUDE"] = "12.5678"
            os.environ["CTRLSOLAR__SITE__TIMEZONE"] = "Europe/Berlin"
            try:
                config = load_config(path)
            finally:
                if previous_lat is None:
                    os.environ.pop("CTRLSOLAR__SITE__LATITUDE", None)
                else:
                    os.environ["CTRLSOLAR__SITE__LATITUDE"] = previous_lat
                if previous_lon is None:
                    os.environ.pop("CTRLSOLAR__SITE__LONGITUDE", None)
                else:
                    os.environ["CTRLSOLAR__SITE__LONGITUDE"] = previous_lon
                if previous_tz is None:
                    os.environ.pop("CTRLSOLAR__SITE__TIMEZONE", None)
                else:
                    os.environ["CTRLSOLAR__SITE__TIMEZONE"] = previous_tz

        self.assertEqual(config.site.latitude, 47.1234)
        self.assertEqual(config.site.longitude, 12.5678)
        self.assertEqual(config.site.timezone, "Europe/Berlin")


if __name__ == "__main__":
    unittest.main()
