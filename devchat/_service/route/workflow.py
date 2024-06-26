from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

import oyaml as yaml
import yaml as pyyaml


from fastapi import APIRouter
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field

from devchat.workflow.namespace import get_prioritized_namespace_path
from devchat.workflow.path import (
    COMMAND_FILENAMES,
    WORKFLOWS_BASE,
    WORKFLOWS_CONFIG_FILENAME,
)
from devchat.workflow.command.update import update_by_git, update_by_zip, copy_workflows_usr

HAS_GIT = False
try:
    from git import GitCommandError, InvalidGitRepositoryError, Repo
except ImportError:
    pass
else:
    HAS_GIT = True

router = APIRouter()


class WorkflowMeta(BaseModel):
    name: str = Field(..., description="workflow name")
    namespace: str = Field(..., description="workflow namespace")
    active: bool = Field(..., description="active flag")
    command_conf: Dict = Field(description="command configuration", default_factory=dict)


@router.get("/")
async def hello():
    return {"hello": "devchat workflow"}


def iter_namespace(
    ns_path: str, existing_names: Set[str]
) -> Tuple[List[WorkflowMeta], Set[str]]:
    """
    Get all workflows under the namespace path.

    Args:
        ns_path: the namespace path
        existing_names: the existing workflow names to check if the workflow is the first priority

    Returns:
        List[WorkflowMeta]: the workflows
        Set[str]: the updated existing workflow names
    """
    root = Path(ns_path)
    interest_files = set(COMMAND_FILENAMES)
    result = []
    unique_names = set(existing_names)
    for file in root.rglob("*"):
        try:
            if file.is_file() and file.name in interest_files:
                rel_path = file.relative_to(root)
                parts = rel_path.parts
                workflow_name = ".".join(parts[:-1])
                is_first = workflow_name not in unique_names

                # load the config content from file
                with open(file, "r", encoding="utf-8") as file_handle:
                    yaml_content = file_handle.read()
                    command_conf = yaml.safe_load(yaml_content)
                    # pop the "steps" field
                    command_conf.pop("steps", None)

                workflow = WorkflowMeta(
                    name=workflow_name,
                    namespace=root.name,
                    active=is_first,
                    command_conf=command_conf,
                )
                unique_names.add(workflow_name)
                result.append(workflow)
        except pyyaml.scanner.ScannerError as err:
            # TODO: log the error
            # logger.error("Failed to load %s: %s", rel_path, err)
            print("Failed to load %s: %s", rel_path, err)
        except Exception as err:
            # TODO: log the error
            # logger.error("Unknown error when loading %s: %s", rel_path, err)
            print("Unknown error when loading %s: %s", rel_path, err)

    return result, unique_names


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


# @router.get("/update")
# async def update_workflows():
#     base_path = Path(WORKFLOWS_BASE)

#     if HAS_GIT:
#         update_by_git(base_path)
#     else:
#         update_by_zip(base_path)

#     copy_workflows_usr()
