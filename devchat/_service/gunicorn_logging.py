import logging
import os
import sys

from gunicorn.app.base import BaseApplication
from gunicorn.glogging import Logger
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


class StubbedGunicornLogger(Logger):
    def setup(self, cfg):
        handler = logging.NullHandler()
        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)
        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)
        self.error_logger.setLevel(config.LOG_LEVEL)
        self.access_logger.setLevel(config.LOG_LEVEL)


class StandaloneApplication(BaseApplication):
    """Our Gunicorn application."""

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def run_with_gunicorn(app):
    intercept_handler = InterceptHandler()
    # logging.basicConfig(handlers=[intercept_handler], level=LOG_LEVEL)
    # logging.root.handlers = [intercept_handler]
    logging.root.setLevel(config.LOG_LEVEL)

    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    workspace_chat_dir = get_workspace_chat_dir(config.WORKSPACE)
    log_file = os.path.join(workspace_chat_dir, config.LOG_FILE)

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

    options = {
        "bind": f"0.0.0.0:{config.PORT}",
        "workers": config.WORKERS,
        "accesslog": "-",
        "errorlog": "-",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "logger_class": StubbedGunicornLogger,
    }

    StandaloneApplication(app, options).run()


# https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
