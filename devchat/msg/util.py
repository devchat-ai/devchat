import os
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Tuple

from devchat.utils import unix_to_local_datetime, user_id
from devchat.workflow.workflow import Workflow

from .path import USER_CHAT_DIR
from .schema import MessageRequest
from .user_info import user_info


class MessageType(Enum):
    """
    Enum for message types
    """

    CHATTING = "chatting"  # chat with LLM directly
    WORKFLOW = "workflow"  # trigger a workflow


def mk_meta() -> Tuple[str, str]:
    """
    Make metadata for a response
    """
    name = user_info.name
    email = user_info.email
    user_str, _ = user_id(name, email)

    _timestamp = datetime.timestamp(datetime.now())
    _local_time = unix_to_local_datetime(_timestamp)
    date_str = _local_time.strftime("%a %b %d %H:%M:%S %Y %z")

    return user_str, date_str


def _ensure_workspace_chat_dir(workspace_path: str) -> str:
    """
    Ensure the workspace chat directory exists and is ignored by git

    return the chat directory path
    """
    assert workspace_path, "workspace path is required to create .chat directory"
    chat_dir = os.path.join(workspace_path, ".chat")

    if not os.path.exists(chat_dir):
        try:
            os.makedirs(chat_dir, exist_ok=True)
        except FileExistsError:
            pass

    # ignore .chat dir in user's workspace
    ignore_file = os.path.join(chat_dir, ".gitignore")
    ignore_content = "*\n"
    if not os.path.exists(ignore_file):
        with open(ignore_file, "w") as f:
            f.write(ignore_content)

    return chat_dir


def get_workspace_chat_dir(workspace_path: Optional[str]) -> str:
    """
    Get the chat directory for a workspace
    Return user chat directory if workspace is None
    """
    workspace_chat_dir = USER_CHAT_DIR
    if workspace_path:
        workspace_chat_dir = _ensure_workspace_chat_dir(workspace_path)

    return workspace_chat_dir


def route_message_by_content(message_content: str) -> Tuple[MessageType, Any]:
    """
    Route the message to the correct handler
    1. trigger a workflow
    2. chat with LLM directly
    """
    content = message_content
    print(f"check content: {content}")

    wf_name, wf_input = Workflow.parse_trigger(content)
    workflow = Workflow.load(wf_name) if wf_name else None

    if workflow:
        # TODO: the message should be handled by the workflow engine
        return MessageType.WORKFLOW, (workflow, wf_name, wf_input)

    else:
        # chat with LLM directly
        return MessageType.CHATTING, None
