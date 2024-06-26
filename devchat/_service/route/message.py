import time
import json

from typing import Dict, Optional, List, Iterator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse


router = APIRouter()


@router.get("/hello")
async def hello():
    return {"hello": "devchat message"}


sample_txt = """
金樽清酒斗十千，玉盘珍羞直万钱。
停杯投箸不能食，拔剑四顾心茫然。
欲渡黄河冰塞川，将登太行雪满山。
闲来垂钓碧溪上，忽复乘舟梦日边。
行路难！行路难！多歧路，今安在？
长风破浪会有时，直挂云帆济沧海。
"""


@router.get("/ssample")
async def sample():

    def _gen():
        # for char in sample_txt:
        #     time.sleep(0.1)
        #     yield char
        lines = sample_txt.split("\n")
        for line in lines:
            time.sleep(0.5)
            yield line + "\n"

    return StreamingResponse(_gen(), media_type="text/plain")


from devchat.msg.util import mk_meta, route_message, MessageType
from devchat.msg.schema import MessageRequest, MessageResponseChunk
from devchat.msg.chatting import chatting
from devchat.workflow.workflow import Workflow


def _mock_gen(
    content: str, user_str: str, date_str: str
) -> Iterator[MessageResponseChunk]:
    yield MessageResponseChunk(
        user=user_str, date=date_str, content="\n\n# mock response\n\n"
    ).json()

    count = 0
    chunk = []
    for c in content:
        count += 1
        chunk.append(c)
        if count % 5 == 0:
            time.sleep(0.2)
            res_chunk = MessageResponseChunk(
                user=user_str, date=date_str, content="".join(chunk)
            )
            a = res_chunk.json()
            yield res_chunk.json()
            chunk = []
    if chunk:
        res_chunk = MessageResponseChunk(
            user=user_str, date=date_str, content="".join(chunk)
        )
        yield res_chunk.json()


@router.post("/msg")
async def msg(
    request: MessageRequest,
):
    print(f"check request: \n{request}")
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
            # # run the workflow

            # workflow.setup(
            #     model_name=request.model_name,
            #     user_input=wf_input,
            #     history_messages=[],  # not in use, will be assistant.prompt.messages if needed
            #     parent_hash=request.parent,
            # )
            # return_code = workflow.run_steps()
            # ret_val = [
            #     f"- the requst content is: \n\n{request.content}\n\n",
            #     f"- workflow return_code: \n\n{return_code}\n\n",
            # ]
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
        content = request.content
        return StreamingResponse(
            _mock_gen(content, user_str, date_str), media_type="application/json"
        )
