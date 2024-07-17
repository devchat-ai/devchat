import logging
import os
import sys

from loguru import logger

from devchat._service.config import config
from devchat.workspace_util import get_workspace_chat_dir


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(config.LOG_LEVEL)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    workspace_chat_dir = get_workspace_chat_dir(config.WORKSPACE)
    log_file = os.path.join(workspace_chat_dir, config.LOG_FILE)

    # configure loguru
    logger.configure(
        handlers=[
            {"sink": sys.stdout, "serialize": config.JSON_LOGS},
            {
                "sink": log_file,
                "serialize": config.JSON_LOGS,
                "rotation": "10 days",
                "retention": "30 days",
                "enqueue": True,
            },
        ]
    )
