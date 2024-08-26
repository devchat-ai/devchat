from pathlib import Path
from typing import List

from devchat.utils import get_logger

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
    CUSTOM_BASE,
    CUSTOM_CONFIG_FILE,
    CHAT_DIR,
    CHAT_CONFIG_FILENAME
)
from devchat.workflow.update_util import (
    HAS_GIT,
    copy_workflows_usr,
    update_by_git,
    update_by_zip,
)

router = APIRouter()

logger = get_logger(__name__)

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

@router.post("/custom_update", response_model=response.UpdateWorkflows)
def update_custom_workflows():
    logger.info(f"Working in update custom workflows.")
    base_path = Path(CUSTOM_BASE)
    custom_config_path = Path(CUSTOM_BASE) / CUSTOM_CONFIG_FILE
    chat_config_path = Path(CHAT_DIR) / CHAT_CONFIG_FILENAME

    if chat_config_path.exists():
        logger.info(f"Read chat config file {chat_config_path}.")
        with open(chat_config_path, "r", encoding="utf-8") as file:
            chat_config_content = yaml.safe_load(file.read())
            
            if "custom_git_urls" in chat_config_content:
                custom_git_urls = chat_config_content["custom_git_urls"]
                logger.info(f"Found custom_git_urls {custom_git_urls}.")
                
                updated_any = True
                update_messages = []

                for url in custom_git_urls:
                    repo_name = url.split("/")[-1].replace(".git", "")  # 提取repo名称
                    repo_path = base_path / repo_name  # 拼接出clone路径
                    candidates_git_urls = [(url, 'main')]
                    
                    logger.info(f"Starting update for {repo_name} at {repo_path} using Git URL on the main branch.")
                    updated, message = update_by_git(repo_path, candidates_git_urls, "main")
                    update_messages.append(f"{repo_name}: {message}")

                    if updated:
                        logger.info(f"Updated repository: {repo_name}")
                        # 更新custom配置文件
                        if custom_config_path.exists():
                            logger.info(f"Updating custom config file {custom_config_path}.")
                            with open(custom_config_path, "r+", encoding="utf-8") as file:
                                custom_config_content = yaml.safe_load(file.read())
                                if repo_name not in custom_config_content.get("namespaces", []):
                                    custom_config_content["namespaces"].insert(0,repo_name)
                                    file.seek(0)
                                    file.truncate()  # 清空文件内容
                                    yaml.safe_dump(custom_config_content, file)
                        else:
                            logger.info(f"Creating custom config file {custom_config_path}.")
                            custom_config_content = {"namespaces": [repo_name]}
                            with open(custom_config_path, "w", encoding="utf-8") as file:
                                yaml.safe_dump(custom_config_content, file)
                    else:
                        updated_any = False if message.index("up-to-date") < 0 else True
                        logger.info(f"No updates made for repository: {repo_name}")

                message_summary = " | ".join(update_messages)
                return response.UpdateWorkflows(updated=updated_any, message=message_summary)
            else:
                return response.UpdateWorkflows(False, "No custom_git_urls found in .chat/config.yaml")
    else:
        return response.UpdateWorkflows(False, "No .chat config found")
