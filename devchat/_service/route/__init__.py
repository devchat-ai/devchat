from fastapi import APIRouter
from .workflow import router as workflow_router
from .message import router as message_router
from .log import router as log_router

router = APIRouter()

router.include_router(workflow_router, prefix="/workflow", tags=["Workflow"])
router.include_router(message_router, prefix="/message", tags=["Message"])
router.include_router(log_router, prefix="/log", tags=["LogManager"])