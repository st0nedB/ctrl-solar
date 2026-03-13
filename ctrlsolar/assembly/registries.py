from ctrlsolar.battery.noah2000 import GroBroFactory
from ctrlsolar.controller.battery import DCBatteryOptimizer
from ctrlsolar.controller.forecast import ProductionForecast
from ctrlsolar.controller.power import ReduceConsumption
from ctrlsolar.inverter.deye import Deye2MqttFactory, DeyeSunM160G4


BATTERY_FACTORIES = {
    "noah2000": GroBroFactory.initialize,
}

INVERTER_FACTORIES = {
    "deye_mqtt": Deye2MqttFactory.initialize,
}

INVERTER_MODELS = {
    "DeyeSunM160G4": DeyeSunM160G4,
}

CONTROLLERS = {
    "dc_battery_optimizer": DCBatteryOptimizer,
    "production_forecast": ProductionForecast,
    "reduce_consumption": ReduceConsumption,
}
