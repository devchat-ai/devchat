from fastapi import APIRouter, HTTPException, status

from devchat._service.schema import request, response
from devchat.msg.log_util import delete_log_prompt, gen_log_prompt, insert_log_prompt

router = APIRouter()


@router.post("/insert", response_model=response.InsertLog)
def insert(
    item: request.InsertLog,
):
    try:
        prompt = gen_log_prompt(item.jsondata, item.filepath)
        prompt_hash = insert_log_prompt(prompt, item.workspace)
    except Exception as e:
        detail = f"Failed to insert log: {str(e)}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    return response.InsertLog(hash=prompt_hash)


@router.post("/delete", response_model=response.DeleteLog)
def delete(
    item: request.DeleteLog,
):
    try:
        success = delete_log_prompt(item.hash, item.workspace)
        if not success:
            detail = f"Failed to delete log <{item.hash}>. Log not found or is not a leaf."
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    except Exception as e:
        detail = f"Failed to delete log <{item.hash}>: {str(e)}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

    return response.DeleteLog(success=success)
