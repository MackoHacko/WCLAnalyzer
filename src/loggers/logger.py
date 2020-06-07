import logging
import logging.config
import os
from pathlib import Path
from flask import request
from typing import Optional

import yaml

LOGGING_CONFIG = os.path.join(os.getcwd(), "configs/logger.yml")


class Logger():
    def __init__(self):
        with open(LOGGING_CONFIG, 'r') as stream:
            self.config = yaml.safe_load(stream)
        logging.config.dictConfig(self.config)

    def getLogger(self, logger_name: str, log_level: Optional[str] = None):
        logger = logging.getLogger(Path(logger_name).stem)
        if log_level:
            logger.setLevel(log_level)
        filt = UserFilter()
        logger.addFilter(filt)
        return logger


class UserFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """

    def filter(self, record):
        try:
            user = request.authorization['username']
        except RuntimeError:
            user = None
        user = "Not yet authorized user" if user is None else str(user)
        record.user = user
        return True
