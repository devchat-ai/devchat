import logging
import os
import sys

from fastapi import FastAPI
from loguru import logger

from devchat._service.config import config
from devchat._service.custom_logging import (
    InterceptHandler,
    StandaloneApplication,
    StubbedGunicornLogger,
)
from devchat._service.route import router
from devchat.workspace_util import get_workspace_chat_dir

api_app = FastAPI(
    title="DevChat Local Service",
)
api_app.mount("/devchat", router)
api_app.include_router(router)


# app = socketio.ASGIApp(sio_app, api_app, socketio_path="devchat.socket")

# NOTE: some references if we want to use socketio with FastAPI in the future

# https://www.reddit.com/r/FastAPI/comments/170awhx/mount_socketio_to_fastapi/
# https://github.com/miguelgrinberg/python-socketio/blob/main/examples/server/asgi/fastapi-fiddle.py


def main():
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

    StandaloneApplication(api_app, options).run()


if __name__ == "__main__":
    main()
