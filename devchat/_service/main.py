from fastapi import FastAPI

from devchat._service.config import config
from devchat._service.route import router
from devchat._service.uvicorn_logging import setup_logging

api_app = FastAPI(
    title="DevChat Local Service",
)
api_app.include_router(router)


# app = socketio.ASGIApp(sio_app, api_app, socketio_path="devchat.socket")

# NOTE: some references if we want to use socketio with FastAPI in the future

# https://www.reddit.com/r/FastAPI/comments/170awhx/mount_socketio_to_fastapi/
# https://github.com/miguelgrinberg/python-socketio/blob/main/examples/server/asgi/fastapi-fiddle.py


def main():
    # Use uvicorn to run the app because gunicorn doesn't support Windows
    from uvicorn import Config, Server

    server = Server(
        Config(
            api_app,
            host="0.0.0.0",
            port=config.PORT,
        ),
    )

    # setup logging last, to make sure no library overwrites it
    # (they shouldn't, but it happens)
    setup_logging()
    server.run()


if __name__ == "__main__":
    main()
