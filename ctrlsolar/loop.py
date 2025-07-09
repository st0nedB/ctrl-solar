import time
from ctrlsolar.controller import Controller
from ctrlsolar.controller.forecast import ProductionForecast
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Loop:
    def __init__(
        self,
        controller: list[Controller] | Controller,
        update_interval: int = 15,
    ):
        if isinstance(controller, Controller):
            controller = [controller]

        self.controller = controller
        self.update_interval = update_interval

    def run(self):
        try:
            while True:
                for cc in self.controller:
                    print()
                    logger.info(f"Update started for {cc.name}.")
                    cc.update()

                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            pass

        return
