# import logging
#
# from project import target

import logging

# import venv.pydoover.cloud
from pydoover.cloud import ProcessorBase, Channel


class target(ProcessorBase):
    def setup(self):
        ...

    def process(self):
        self._log_handler.logs.append("test")
        logging.info("Hello World Started...")

        logging.debug("Triggerred by: %s", self.task_id)

        hello_world_channel = self.fetch_channel_named("josh-test")
        hello_world_channel.publish('Hello World1')

        logging.info("Hello World Finished")

    def close(self):
        ...
