import const

import logging

logger = logging.getLogger(__name__)
logger.setLevel(const.LOGGING_LEVEL)

for logger_handler in const.LOGGING_HANDLERS:
    logger.addHandler(logger_handler)
