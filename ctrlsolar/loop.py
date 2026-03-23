from ctrlsolar.abstracts import Controller
import time
import logging

logger = logging.getLogger(__name__)

class Loop:
    def __init__(
        self,
        controller: list[Controller] | Controller,
        update_interval: int = 60,
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
                    logger.info(f"-----------------------------")
                    cc.update()

                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            pass

        return
