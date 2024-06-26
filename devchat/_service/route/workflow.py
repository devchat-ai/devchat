from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

import oyaml as yaml


from fastapi import APIRouter
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field

from devchat.workflow.namespace import (
    get_prioritized_namespace_path,
    iter_namespace,
    WorkflowMeta,
)
from devchat.workflow.path import (
    COMMAND_FILENAMES,
    WORKFLOWS_BASE,
    WORKFLOWS_CONFIG_FILENAME,
)
from devchat.workflow.update_util import (
    update_by_git,
    update_by_zip,
    HAS_GIT,
    copy_workflows_usr,
)


router = APIRouter()


@router.get("/")
async def hello():
    return {"hello": "devchat workflow"}


# TODO: handle errors
@router.get("/list", response_model=List[WorkflowMeta])
async def list_workflow():
    namespace_paths = get_prioritized_namespace_path()

    workflows: List[WorkflowMeta] = []
    visited_names = set()
    for ns_path in namespace_paths:
        ws_names, visited_names = iter_namespace(ns_path, visited_names)
        workflows.extend(ws_names)

    return workflows


@router.get("/config")
async def get_config():
    config_path = Path(WORKFLOWS_BASE) / WORKFLOWS_CONFIG_FILENAME
    config_content = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as file:
            config_content = yaml.safe_load(file.read())

    return JSONResponse(content=config_content)


class UpdateWorkflows(BaseModel):
    updated: bool = Field(..., description="Whether the workflows are updated.")
    message: str = Field(..., description="The message of the update.")


# TODO: set time out? what if the update takes too long due to user's network?
@router.post("/update", response_model=UpdateWorkflows)
async def update_workflows():
    base_path = Path(WORKFLOWS_BASE)

    if HAS_GIT:
        updated, message = update_by_git(base_path)
    else:
        updated, message = update_by_zip(base_path)

    copy_workflows_usr()

    return UpdateWorkflows(updated=updated, message=message)
