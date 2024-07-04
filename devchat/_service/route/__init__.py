from fastapi import APIRouter

from .logs import router as log_router
from .message import router as message_router
from .topics import router as topic_router
from .workflow import router as workflow_router

router = APIRouter()

router.include_router(workflow_router, prefix="/workflow", tags=["Workflow"])
router.include_router(message_router, prefix="/message", tags=["Message"])
router.include_router(log_router, prefix="/logs", tags=["LogManagement"])
router.include_router(topic_router, prefix="/topics", tags=["TopicManagement"])
