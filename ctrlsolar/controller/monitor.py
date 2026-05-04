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
    HOURLY_SOLAR_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE,
    HOURLY_SOLAR_PRODUCTION_STATE_TOPIC_TEMPLATE,
    HOURLY_AC_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE,
    HOURLY_AC_PRODUCTION_STATE_TOPIC_TEMPLATE,
)

logger = logging.getLogger(__name__)


class EnergyMonitor(Controller):
    def __init__(self, battery: DCCoupledBattery, ac_sensor: Optional[Type[Sensor]]):
        self._deviceid = battery.serial_number
        self._solar_energy = battery
        self._ac_energy = ac_sensor
        self._previous_ac_energy = None
        self._previous_solar_energy = None
        self._hour: int = 0
        self._day = datetime.now(get_timezone()).day
        self._ac_energy_tracker = dict(zip(range(24), 24 * [0.0]))
        self._solar_energy_tracker = dict(zip(range(24), 24 * [0.0]))

    def _reset_energy_tracker(self):
        day = datetime.now(get_timezone()).day
        hour = datetime.now(get_timezone()).hour
        if day != self._day:
            self._ac_energy_tracker = dict(zip(range(24), 24 * [0.0]))
            self._solar_energy_tracker = dict(zip(range(24), 24 * [0.0]))
            self._day = day

        if hour != self._hour:
            self._ac_energy_tracker[hour] = 0.0
            self._solar_energy_tracker[hour] = 0.0
            self._hour = hour

        if self._previous_ac_energy is None:
            # only called at init
            self._previous_solar_energy = self._solar_energy.energy_out

        if self._ac_energy is not None:
            if self._previous_ac_energy is None:
                self._previous_ac_energy = self._ac_energy.value

        return

    def update(self):
        self._reset_energy_tracker()
        # TODO: Make a better abstraction for the sensor property
        if any_is_none(self._solar_energy.energy_out, self._previous_solar_energy):  # type: ignore
            logger.warning("Skipping update!")
            return

        solar_energy = self._solar_energy.energy_out
        previous_solar_energy = cast(float, self._previous_solar_energy)

        hour = datetime.now(get_timezone()).hour
        delta = solar_energy - previous_solar_energy

        if delta < 0:
            logger.warning(
                f"Measured a negative energy production, but should be strictly positive. Not updating!"
            )
        else:
            logger.info(f"Detected a delta={delta:.2f} Wh.")
            self._solar_energy_tracker[hour] += delta
            self._previous_solar_energy = solar_energy

        if self._ac_energy is not None:
            if any_is_none(self._ac_energy.value, self._previous_ac_energy):
                logger.warning("Skipping update!")
                return

            prod_energy = cast(float, self._ac_energy.value)
            previous_ac_energy = cast(float, self._previous_ac_energy)

            hour = datetime.now(get_timezone()).hour
            delta = prod_energy - previous_ac_energy

            if delta < 0:
                logger.warning(
                    f"Measured a negative energy production, but should be strictly positive. Not updating!"
                )
            else:
                logger.info(f"Detected a delta={delta:.2f} Wh.")
                self._ac_energy_tracker[hour] += delta
                self._previous_ac_energy = prod_energy

        self._publish()
        return

    def _publish(self):
        mqtt = get_mqtt()
        mqtt.publish(
            HOURLY_SOLAR_PRODUCTION_STATE_TOPIC_TEMPLATE.format(device_id=self._deviceid),
            datetime.now(get_timezone()).date().isoformat(),
        )
        mqtt.publish(
            HOURLY_SOLAR_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE.format(
                device_id=self._deviceid
            ),
            {hour: round(value, 2) for hour, value in self._solar_energy_tracker.items()},
        )

        if self._ac_energy is not None:
            mqtt.publish(
                HOURLY_AC_PRODUCTION_STATE_TOPIC_TEMPLATE.format(device_id=self._deviceid),
                datetime.now(get_timezone()).date().isoformat(),
            )
            mqtt.publish(
                HOURLY_AC_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE.format(
                    device_id=self._deviceid
                ),
                {hour: round(value, 2) for hour, value in self._ac_energy_tracker.items()},
            )

        return
