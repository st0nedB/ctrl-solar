from ctrlsolar.abstracts import Sensor, Inverter, Controller
from ctrlsolar.functions import check_properties
import logging

logger = logging.getLogger(__name__)


class ReduceConsumption(Controller):
    name: str = "ReduceConsumption"

    def __init__(
        self,
        inverter: Inverter,
        meter: Sensor,
        control_threshold_W: float = 50.0,
        max_power_W: float = 800.0,
        min_power_W: float = 80.0,
        offset_W: float = -10.0,
    ):
        self.inverter = inverter
        self.meter = meter
        self.control_threshold = control_threshold_W
        self.max_power_W = max_power_W
        self.min_power_W = min_power_W
        self.offset_W = offset_W
        self.active = True

    def _check_empty_sensors_readings(self) -> bool:
        empty_sensors_readings: list[bool] = []
        entities = (self.inverter, self.meter)

        for entity in entities:
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
        production = self.inverter.production
        limit = self.inverter.production_limit

        if self._check_empty_sensors_readings():
            logger.warning(
                "Found `None` in one or multiple sensor readings. Update is skipped."
            )
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
            "Production limit\t{x}".format(
                x=f"{limit:.1f} W" if limit is not None else "N/A"
            )
        )

        if not skip_update:
            # Calculate power imbalance
            # Positive consumption means we're importing from grid (need more production)
            # Negative consumption means we're exporting to grid (need less production)
            logger.info(f"Consumption \t{consumption:.1f} W {'(importing)' if consumption > 0 else '(exporting)' if consumption < 0 else '(balanced)'}")
                
            # Check if adjustment is needed
            if abs(consumption) > self.control_threshold:
                logger.info(f"Consumption of {consumption:.1f} W exceeds control threshold of {self.control_threshold:.1f} W")

                new_limit = limit + consumption + self.offset_W  # type: ignore
                
                # Apply maximum power constraint
                if new_limit > self.max_power_W:
                    logger.info(f"Calculated limit {new_limit:.1f} W exceeds {self.max_power_W:.1f} W, capping to max.")
                    new_limit = self.max_power_W
                elif new_limit < self.min_power_W:
                    logger.info(f"Calculated limit {new_limit:.1f} W is below {self.min_power_W:.1f} W, capping to min.")
                    new_limit = self.min_power_W

                logger.info(f"New production limit: {new_limit:.1f} W (change: {new_limit - limit:.1f} W)")  # type: ignore

                # Apply the new limit
                self.inverter.production_limit = new_limit
                logger.info(f"Production limit updated to {new_limit:.1f} W")

            else:
                logger.info(f"Power imbalance {consumption:.1f} W is within control threshold ±{self.control_threshold:.1f} W - no adjustment needed")

        return
