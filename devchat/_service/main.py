from fastapi import FastAPI

from devchat._service.route import router
from dotenv import load_dotenv
# import socketio
import uvicorn

# from devchat._service.route.async_socket import sio_app

# TODO: manage env variables
load_dotenv()


fa_app = FastAPI(
    title="DevChat Local Service",
)
fa_app.mount("/devchat", router)
fa_app.include_router(router)

# app = socketio.ASGIApp(sio_app, fa_app, socketio_path="devchat.socket")

if __name__ == '__main__':
    # uvicorn.run("devchat._service.main:app", host='127.0.0.1', port=22222, reload=True)
    uvicorn.run("devchat._service.main:fa_app", host='127.0.0.1', port=22222, reload=True)


# https://www.reddit.com/r/FastAPI/comments/170awhx/mount_socketio_to_fastapi/
# https://github.com/miguelgrinberg/python-socketio/blob/main/examples/server/asgi/fastapi-fiddle.py
# not work: https://github.com/tiangolo/fastapi/discussions/8781

