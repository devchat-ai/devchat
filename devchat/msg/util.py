from datetime import datetime
from enum import Enum
from typing import Any, Tuple

from devchat.utils import unix_to_local_datetime, user_id
from devchat.workflow.workflow import Workflow

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


def route_message_by_content(message_content: str) -> Tuple[MessageType, Any]:
    """
    Route the message to the correct handler
    1. trigger a workflow
    2. chat with LLM directly
    """
    content = message_content

    wf_name, wf_input = Workflow.parse_trigger(content)
    workflow = Workflow.load(wf_name) if wf_name else None

    if workflow:
        # the message should be handled by the workflow engine
        return MessageType.WORKFLOW, (workflow, wf_name, wf_input)

    else:
        # chat with LLM directly
        return MessageType.CHATTING, None
