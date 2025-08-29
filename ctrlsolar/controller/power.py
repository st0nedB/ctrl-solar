from ctrlsolar.inverter import Inverter
from ctrlsolar.io.io import Sensor
from ctrlsolar.controller.controller import Controller
from ctrlsolar.functions import check_properties
import logging

logger = logging.getLogger(__name__)


class ReduceConsumption(Controller):
    name: str = "ReduceConsumption"

    def __init__(
        self,
        inverter: Inverter,
        meter: Sensor,
        available: Sensor,
        control_threshold: float = 50.0,
        max_power: float = 800.0,
        min_power: float = 80.0,
        offset: float = -10.0,
    ):
        self.inverter = inverter
        self.meter = meter
        self.available = available
        self.control_threshold = control_threshold
        self.max_power = max_power
        self.min_power = min_power
        self.offset = offset
        self.active = True

    def _check_empty_sensors_readings(self) -> bool:
        empty_sensors_readings = []
        for entity in [self.inverter, self.meter, self.available]:
            check = check_properties(entity)
            empty = False
            for key, value in check.items():
                if value is False:
                    empty = True
                    logger.debug(f"Reading of '{key}' is `None`.")

            if empty:
                logger.warning(f"Found empty sensor readings.")

            empty_sensors_readings.append(empty)

        return any(empty_sensors_readings)

    def update(self):
        skip_update = True

        consumption = self.meter.get()
        available = self.available.get()
        production = self.inverter.production
        limit = self.inverter.production_limit

        if self._check_empty_sensors_readings():
            logger.warning(
                "Found `None` in one or multiple sensor readings. Update is skipped."
            )
        elif not available:
            logger.info("No production capacity available. Update skipped.")
        else:
            skip_update = False



        logger.info(
            "Consumption\t\t{x}".format(
                x=f"{consumption:.1f} W" if consumption is not None else "N/A"
            )
        )
        logger.info(
            "Production\t\t{x}".format(
                x=f"{production:.1f} W" if production is not None else "N/A"
            )
        )
        logger.info(
            "Production Limit\t{x}".format(
                x=f"{limit:.1f} W" if limit is not None else "N/A"
            )
        )
        logger.info(
            "Power available?\t{x}".format(
                x=f"{available}" if available is not None else "N/A"
            )
        )

        if not skip_update:
            # Calculate power imbalance
            # Positive consumption means we're importing from grid (need more production)
            # Negative consumption means we're exporting to grid (need less production)
            logger.info(f"Consumption \t\t{consumption:.1f} W {'(importing)' if consumption > 0 else '(exporting)' if consumption < 0 else '(balanced)'}")

            # Check if adjustment is needed
            if abs(consumption) > self.control_threshold:
                logger.info(f"Consumption of {consumption:.1f} W exceeds control threshold of {self.control_threshold:.1f} W")

                new_limit = limit + consumption + self.offset  # type: ignore
                
                # Apply maximum power constraint
                if new_limit > self.max_power:
                    logger.info(f"Calculated limit {new_limit:.1f} W exceeds {self.max_power:.1f} W, capping to max.")
                    new_limit = self.max_power
                elif new_limit < self.min_power:
                    logger.info(f"Calculated limit {new_limit:.1f} W is below {self.min_power:.1f} W, capping to min.")
                    new_limit = self.min_power

                logger.info(f"New production limit: {new_limit:.1f} W (change: {new_limit - limit:.1f} W)")  # type: ignore

                # Apply the new limit
                self.inverter.production_limit = new_limit
                logger.info(f"✓ Production limit updated to {new_limit:.1f} W")

            else:
                logger.info(f"Power imbalance {consumption:.1f} W is within control threshold ±{self.control_threshold:.1f} W - no adjustment needed")

        return
