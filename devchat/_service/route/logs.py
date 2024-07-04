from fastapi import APIRouter

from devchat._service.schema import request, response
from devchat.msg.log_util import delete_log_prompt, gen_log_prompt, insert_log_prompt

router = APIRouter()


@router.post("/insert", response_model=response.InsertLog)
async def insert(
    item: request.InsertLog,
):
    # TODO: handle error
    error_msg = None
    prompt = gen_log_prompt(item.jsondata, item.filepath)

    insert_log_prompt(prompt, item.workspace)
    return response.InsertLog(hash=prompt.hash, error=error_msg)


@router.post("/delete")
async def delete(
    item: request.DeleteLog,
):
    print(f"\n\ncheck delete log request: \n{item}")

    success, error_msg = delete_log_prompt(item.hash, item.workspace)

    return response.DeleteLog(success=success, error=error_msg)
