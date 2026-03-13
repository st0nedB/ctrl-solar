import os
import tempfile
import textwrap
import unittest

from ctrlsolar.app import create_app


class RuntimeBuilderTests(unittest.TestCase):
    def test_create_app_builds_runtime_from_config(self):
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
                use_smoothing: true
                panels:
                  - tilt: 45
                    azimuth: 180
                    area: 2.0
                    efficiency: 0.22
              - type: noah2000
                serial: BAT002
                stack_count: 2
                use_smoothing: false
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
                scale: 1.0
              smoothing:
                kind: average
                source_interval: 10
            inverter:
              model: DeyeSunM160G4
              transport: deye_mqtt
              topic_prefix: deye
            controllers:
              - type: dc_battery_optimizer
                full_threshold: 0.95
              - type: reduce_consumption
                max_power: 600
                min_power: 80
                control_threshold_W: 50
                offset: -10.0
              - type: production_forecast
            loop:
              update_interval: 60
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(config_text)
            app = create_app(path)

        self.assertEqual(app.loop.update_interval, 60)
        self.assertEqual(len(app.batteries), 2)
        self.assertEqual(len(app.controllers), 3)
        self.assertEqual(app.controllers[0].name, "DCBatteryOptimizer")
        self.assertEqual(app.controllers[1].name, "ReduceConsumption")
        self.assertEqual(app.controllers[2].name, "ProductionForecast")

    def test_disabled_controller_is_not_built(self):
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
              - type: production_forecast
                enabled: false
            loop:
              update_interval: 60
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(config_text)
            app = create_app(path)

        self.assertEqual(len(app.controllers), 1)
        self.assertEqual(app.controllers[0].name, "ReduceConsumption")


if __name__ == "__main__":
    unittest.main()
