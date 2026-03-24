from ctrlsolar.abstracts import Controller
import time
import logging

logger = logging.getLogger(__name__)

class Loop:
    def __init__(
        self,
        controllers: list[Controller] | Controller,
        update_interval: int = 60,
    ):
        if isinstance(controllers, Controller):
            controllers = [controllers]

        self.controllers = controllers
        self.update_interval = update_interval

    def run(self):
        try:
            while True:
                for cc in self.controllers:
                    print()
                    info = f"Update started for {cc.name}."
                    logger.info(info)
                    logger.info(len(info) * "-")
                    cc.update()

                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            pass

        return
