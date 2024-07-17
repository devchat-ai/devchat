import os
from typing import Iterator, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from devchat._service.schema import request, response
from devchat.msg.chatting import chatting
from devchat.msg.util import MessageType, mk_meta, route_message_by_content
from devchat.workflow.workflow import Workflow

router = APIRouter()


@router.post("/msg")
def msg(
    message: request.UserMessage,
):
    if message.api_key:
        os.environ["OPENAI_API_KEY"] = message.api_key
    if message.api_base:
        os.environ["OPENAI_API_BASE"] = message.api_base

    user_str, date_str = mk_meta()

    message_type, extra = route_message_by_content(message.content)

    if message_type == MessageType.CHATTING:

        def gen_chat_response() -> Iterator[response.MessageCompletionChunk]:
            try:
                for res in chatting(
                    content=message.content,
                    model_name=message.model_name,
                    parent=message.parent,
                    workspace=message.workspace,
                    context_files=message.context,
                ):
                    chunk = response.MessageCompletionChunk(
                        user=user_str,
                        date=date_str,
                        content=res,
                    )
                    yield chunk.json()
            except Exception as e:
                chunk = response.MessageCompletionChunk(
                    user=user_str,
                    date=date_str,
                    content=str(e),
                    isError=True,
                )
                yield chunk.json()
                raise e

        return StreamingResponse(gen_chat_response(), media_type="application/json")

    elif message_type == MessageType.WORKFLOW:
        workflow: Workflow
        wf_name: str
        wf_input: Optional[str]
        workflow, wf_name, wf_input = extra

        if workflow.should_show_help(wf_input):
            doc = workflow.get_help_doc(wf_input)

            def _gen_res_help() -> Iterator[response.MessageCompletionChunk]:
                yield response.MessageCompletionChunk(
                    user=user_str, date=date_str, content=doc
                ).json()

            return StreamingResponse(_gen_res_help(), media_type="application/json")
        else:
            # return "should run workflow" response
            # then the client will trigger the workflow by devchat cli
            def _gen_res_run_workflow() -> Iterator[response.MessageCompletionChunk]:
                yield response.MessageCompletionChunk(
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
        # Should not reach here
        chunk = response.MessageCompletionChunk(
            user=user_str,
            date=date_str,
            content="",
        )
        return StreamingResponse((chunk.json() for _ in [1]), media_type="application/json")
