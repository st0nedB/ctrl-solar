from ctrlsolar.battery.abstract import DCCoupledBattery
from ctrlsolar.controller.abstract import Controller
from ctrlsolar.mqtt.abstract import Sensor
from ctrlsolar.mqtt.mqtt import get_mqtt
from ctrlsolar.localization import get_timezone
from ctrlsolar.utils import any_is_none
from datetime import datetime 
from typing import Optional, Type, cast
import logging
from ctrlsolar.mqtt.topics import (
    HOURLY_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE,
    HOURLY_PRODUCTION_STATE_TOPIC_TEMPLATE,
)


logger = logging.getLogger(__name__)

class EnergyMonitor(Controller):
    def __init__(self, battery: DCCoupledBattery, sensor: Optional[Type[Sensor]]):
        self._deviceid = battery.serial_number
        self._energy = sensor.value if sensor is not None else battery.energy_out
        self._previous_energy = None
        self._hour: int = 0
        self._day = datetime.now(get_timezone()).day  
        self._energy_tracker = dict(zip(range(24), 24*[0.]))
        self._dcac_efficiency = dict(zip(range(24), 24*[0.]))

    def _reset_energy_tracker(self):
        day = datetime.now(get_timezone()).day
        hour = datetime.now(get_timezone()).hour
        if day != self._day:
            self._energy_tracker = dict(zip(range(24), 24*[0.]))
            self._day = day

        if hour != self._hour:
            self._energy_tracker[hour] = 0.0
            self._hour = hour

        if self._previous_energy == None:
            # only called at init
            self._previous_energy = self._energy

        return        

    def update(self):
        self._reset_energy_tracker()
        if any_is_none(self._energy, self._previous_energy):
            logger.warning("Skipping update!")
            return 
        
        energy = cast(float, self._energy)
        previous_energy = cast(float, self._previous_energy) 

        hour = datetime.now(get_timezone()).hour
        delta = energy - previous_energy

        if delta < 0:
            logger.warning(f"Measured a negative energy production, but should be strictly positive. Not updating!")
        else:
            logger.info(f"Detected a delta={delta:.2f} Wh.")
            self._energy_tracker[hour] += delta
            self._previous_energy = self._energy

        self._publish()
        return

    def _publish(self):
        mqtt = get_mqtt()
        mqtt.publish(
            HOURLY_PRODUCTION_STATE_TOPIC_TEMPLATE.format(device_id=self._deviceid),
            datetime.now(get_timezone()).date().isoformat(),
        )
        mqtt.publish(
            HOURLY_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE.format(device_id=self._deviceid),
            {hour: round(value, 2) for hour, value in self._energy_tracker.items()},
        )

        return 