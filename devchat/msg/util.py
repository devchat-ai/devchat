from typing import Tuple, Any
from enum import Enum
from devchat.utils import get_user_info, user_id, unix_to_local_datetime
from datetime import datetime

from .schema import MessageRequest

from devchat.workflow.workflow import Workflow


class MessageType(Enum):
    """
    Enum for message types
    """

    CHATTING = "chatting"  # chat with LLM directly
    WORKFLOW = "workflow"  # trigger a workflow


# TODO: tmp mock value
def mock_get_user_info():
    return "bismarck", "golden@retriver"


def mk_meta() -> Tuple[str, str]:
    """
    Make metadata for a response

    """
    # TODO: tmp mock value
    user_name, user_email = mock_get_user_info()
    user_str, _ = user_id(user_name, user_email)
    # date =
    _timestamp = datetime.timestamp(datetime.now())
    _local_time = unix_to_local_datetime(_timestamp)
    date_str = _local_time.strftime("%a %b %d %H:%M:%S %Y %z")

    return user_str, date_str


def route_message(msg_req: MessageRequest) -> Tuple[MessageType, Any]:
    """
    Route the message to the correct handler
    1. trigger a workflow
    2. chat with LLM directly
    """
    content = msg_req.content
    print(f"check content: {content}")

    wf_name, wf_input = Workflow.parse_trigger(content)
    workflow = Workflow.load(wf_name) if wf_name else None

    if workflow:
        # TODO: the message should be handled by the workflow engine
        return MessageType.WORKFLOW, (workflow, wf_name, wf_input)

    else:
        # chat with LLM directly
        return MessageType.CHATTING, None
