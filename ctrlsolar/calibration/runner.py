from ctrlsolar.battery.abstract import DCCoupledBattery
from ctrlsolar.calibration.abstract import CalibrationSensor


class DCACEfficiency:
    def __init__(self, battery: DCCoupledBattery, sensor: CalibrationSensor):
        self._power_levels = range(50, battery.max_power, 50)
        pass

    def _save_result(self):
        pass

    def run(self):
        # 
        pass


class LocalCorrectionCoefficient:
    def __init__(self):
        pass
    