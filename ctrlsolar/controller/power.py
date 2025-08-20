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
        control_threshold: float = 50.0,
        max_power: float = 800.0,
        offset: float = -10.0,
    ):
        self.inverter = inverter
        self.control_threshold = control_threshold
        self.max_power = max_power
        self.offset = offset
        self.active = True
        self.meter = meter

    def _check_empty_sensors_readings(self) -> bool:
        empty_sensors_readings = []
        for entity in [self.inverter, self.meter]:
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

        if not self._check_empty_sensors_readings():
            skip_update = False
        else:
            logger.warning(
                "Found `None` in one or multiple sensor readings. Update is skipped."
            )

        consumption = self.meter.get()
        production = self.inverter.production
        limit = self.inverter.production_limit

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

        if not skip_update:
            # consumption = requirement - production
            #     ^       =      ^            ^
            #     |              |            |
            #  measured     calculated     measured
            # requirement = consumption + production

            # -> consumption should be zero, so ideally requirement = production
            requirement = consumption + production  # type: ignore
            logger.info(f"Requirement\t\t{requirement:.1f} W")

            # new_limit = limit
            if abs(requirement - production) > self.control_threshold:  # type: ignore
                logger.info(
                    f"Difference of {requirement-production:.1f} W exceeds {self.control_threshold:.1f} W."  # type: ignore
                )

                if requirement < 0:
                    new_limit = (
                        limit + requirement + self.offset  # type: ignore
                    )  # requirement is negative, producing too much. Reduce current limit by that amount
                else:  # requirement > 0:
                    new_limit = requirement + self.offset

                if new_limit >= self.max_power:
                    logger.info(
                        f"Requirement of {requirement:.1f} W exceeds specified maximum of {self.max_power:.1f}W."
                    )
                    new_limit = self.max_power

                logger.info(f"Evaluated new limit {new_limit:.1f} W")

                if abs(new_limit - limit) < self.control_threshold:  # type: ignore
                    # previously set limit is still probably still being set, dont change
                    logger.info(
                        f"Difference between new limit of {new_limit:.1f} W and current limit of {limit:.1f} W is smaller than {self.control_threshold:.1f} W."
                    )
                    new_limit = limit

                if (new_limit != limit) and (new_limit is not None):
                    self.inverter.production_limit = new_limit
                    logger.info(f"Set limit to {new_limit:.1f} W")
                else:
                    logger.info(f"Current limit of {limit:.1f} W is sufficient. No update required.")

            else:
                logger.info(
                    f"No update required (threshold={self.control_threshold:.1f} W)."
                )

        return
