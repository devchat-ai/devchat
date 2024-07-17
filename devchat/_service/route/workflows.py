from pathlib import Path
from typing import List

import oyaml as yaml
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from devchat._service.schema import response
from devchat.workflow.namespace import (
    WorkflowMeta,
    get_prioritized_namespace_path,
    iter_namespace,
)
from devchat.workflow.path import (
    WORKFLOWS_BASE,
    WORKFLOWS_CONFIG_FILENAME,
)
from devchat.workflow.update_util import (
    HAS_GIT,
    copy_workflows_usr,
    update_by_git,
    update_by_zip,
)

router = APIRouter()


@router.get("/list", response_model=List[WorkflowMeta])
def list_workflow():
    namespace_paths = get_prioritized_namespace_path()

    workflows: List[WorkflowMeta] = []
    visited_names = set()
    for ns_path in namespace_paths:
        ws_names, visited_names = iter_namespace(ns_path, visited_names)
        workflows.extend(ws_names)

    return workflows


@router.get("/config")
def get_config():
    config_path = Path(WORKFLOWS_BASE) / WORKFLOWS_CONFIG_FILENAME
    config_content = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as file:
            config_content = yaml.safe_load(file.read())

    return JSONResponse(content=config_content)


@router.post("/update", response_model=response.UpdateWorkflows)
def update_workflows():
    base_path = Path(WORKFLOWS_BASE)

    if HAS_GIT:
        updated, message = update_by_git(base_path)
    else:
        updated, message = update_by_zip(base_path)

    copy_workflows_usr()

    return response.UpdateWorkflows(updated=updated, message=message)
