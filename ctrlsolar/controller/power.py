from collections import deque
from ctrlsolar.inverter import Inverter
from ctrlsolar.io.io import Sensor
from ctrlsolar.controller.controller import Controller
from ctrlsolar.battery.battery import Battery
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)


class ZeroConsumptionController(Controller):
    name: str = "ZeroConsumptionController"

    def __init__(
        self,
        inverter: Inverter,
        meter: Sensor,
        battery: Optional[Battery] = None,
        control_threshold: float = 30.0,
        max_power: float = 800.0,
        smoothen: float = 0.5,
        offset: float = -10.0,
        last_k: int = 3,
    ):
        self.inverter = inverter
        self.meter = meter
        self.battery = battery
        self.control_threshold = control_threshold
        self.max_power = max_power
        self.smoothen = smoothen
        self.offset = offset
        self.diffs = deque(maxlen=last_k)
        self.active = True

    def update(self):
        skip_update = False

        if self.battery is None:
            battery = None
        else:
            battery = self.battery.get_available_power()
            if battery is None:
                logger.warning(f"Reading of `availale` is `None`.")
                skip_update = True
            else:
                if battery == 0:
                    skip_update = True

        consumption = self.meter.get()
        if consumption is None:
            logger.warning(f"Reading of `meter` is `None`.")
            skip_update = True

        production = self.inverter.get_production()
        if production is None:
            logger.warning(f"Reading of `inverter prodcution` is `None`.")
            skip_update = True

        limit = self.inverter.get_production_limit()
        if limit is None:
            logger.warning(f"Reading of `inverter limit` is `None`.")
            skip_update = True

        logger.info("Consumption\t\t{x}".format(x=f"{consumption:.2f}W" if consumption is not None else "N/A"))
        logger.info("Production\t\t\t{x}".format(x=f"{production:.2f}W" if production is not None else "N/A"))
        logger.info("Battery\t\t\t{x}".format(x=f"{battery:.2f}W" if battery is not None else "N/A"))
        logger.info("Production Limit\t\t{x}".format(x=f"{limit:.2f}W" if limit is not None else "N/A"))

        if not skip_update:
            # consumption = requirement - production
            #     ^       =      ^            ^
            #     |              |            |
            #  measured     calculated     measured
            # requirement = consumption + production

            # -> consumption should be zero, so ideally requirement = production
            requirement = consumption + production
            logger.info(f"Requirement\t\t{requirement:.2f}W")

            new_limit = limit
            if abs(requirement - production) > self.control_threshold:
                logger.info(
                    f"Difference of {requirement-production:.2f}W exceeds {self.control_threshold:.2f}W."
                )

                new_limit = requirement + self.offset
                if new_limit >= self.max_power:
                    logger.info(f"Requirement of {requirement}W exceeds specified maximum of {self.max_power}W.")
                    new_limit = self.max_power

            logger.info(f"Evaluated new limit {new_limit:.2f}W")

            if (new_limit != limit) and (new_limit is not None):
                self.inverter.set_production_limit(new_limit)
                logger.info(f"Set limit to {new_limit:.2f}W")

            else:
                logger.info(
                    f"No update required (threshold={self.control_threshold:.2f}W)."
                )
        else:
            logger.info(
                f"Found `None` in one or multiple sensor readings. Update is skipped."
            )

        return
