import time
import json
import os

from typing import Dict, Optional, List, Iterator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse


router = APIRouter()


@router.get("/hello")
async def hello():
    return {"hello": "devchat message"}


from devchat.msg.util import mk_meta, route_message, MessageType
from devchat.msg.schema import MessageRequest, MessageResponseChunk
from devchat.msg.chatting import chatting
from devchat.workflow.workflow import Workflow


@router.post("/msg")
async def msg(
    request: MessageRequest,
):
    if request.api_key:
        os.environ["OPENAI_API_KEY"] = request.api_key
    if request.api_base:
        os.environ["OPENAI_API_BASE"] = request.api_base

    user_str, date_str = mk_meta()

    message_type, extra = route_message(request)
    print(f"message type: {message_type}")

    if message_type == MessageType.CHATTING:

        def gen_chat_response() -> Iterator[MessageResponseChunk]:
            for res in chatting(request):
                chunk = MessageResponseChunk(user=user_str, date=date_str, content=res)
                yield chunk.json()

        return StreamingResponse(gen_chat_response(), media_type="application/json")

    elif message_type == MessageType.WORKFLOW:
        workflow: Workflow
        wf_name: str
        wf_input: Optional[str]
        workflow, wf_name, wf_input = extra

        if workflow.should_show_help(wf_input):

            doc = workflow.get_help_doc(wf_input)

            def _gen_res_help() -> Iterator[MessageResponseChunk]:
                yield MessageResponseChunk(
                    user=user_str, date=date_str, content=doc
                ).json()

            return StreamingResponse(_gen_res_help(), media_type="application/json")
        else:
            # return "should run workflow" response
            # then the client will trigger the workflow by devchat cli
            def _gen_res_run_workflow() -> Iterator[MessageResponseChunk]:
                yield MessageResponseChunk(
                    user=user_str,
                    date=date_str,
                    content="",
                    finish_reason="should_run_workflow",
                    extra={"workflow_name": wf_name, "workflow_input": wf_input},
                ).json()

            return StreamingResponse(
                _gen_res_run_workflow(),
                media_type="application/json",
            )

    else:
        # TODO: Should not reach here
        chunk = MessageResponseChunk(user=user_str, date=date_str, content="")
        return StreamingResponse(
            (chunk.json() for _ in [1]), media_type="application/json"
        )
