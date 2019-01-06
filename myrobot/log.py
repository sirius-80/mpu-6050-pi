import logging


class Log:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)


