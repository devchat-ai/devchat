from fastapi import FastAPI

from devchat._service.route import router

api_app = FastAPI(
    title="DevChat Local Service",
)
api_app.mount("/devchat", router)
api_app.include_router(router)


# app = socketio.ASGIApp(sio_app, api_app, socketio_path="devchat.socket")

# NOTE: some references if we want to use socketio with FastAPI in the future

# https://www.reddit.com/r/FastAPI/comments/170awhx/mount_socketio_to_fastapi/
# https://github.com/miguelgrinberg/python-socketio/blob/main/examples/server/asgi/fastapi-fiddle.py
