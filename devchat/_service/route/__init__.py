from fastapi import APIRouter

from .logs import router as log_router
from .message import router as message_router
from .topics import router as topic_router
from .workflows import router as workflow_router

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"message": "pong"}


router.include_router(workflow_router, prefix="/workflows", tags=["WorkflowManagement"])
router.include_router(message_router, prefix="/message", tags=["Message"])
router.include_router(log_router, prefix="/logs", tags=["LogManagement"])
router.include_router(topic_router, prefix="/topics", tags=["TopicManagement"])
