from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from devchat.msg.log_util import delete_log_prompt, gen_log_prompt, insert_log_prompt

router = APIRouter()


class InsertLogRequest(BaseModel):
    workspace: Optional[str] = Field(None, description="absolute path to the workspace/repository")
    jsondata: Optional[str] = Field(None, description="data to insert in json format")
    filepath: Optional[str] = Field(None, description="file path to insert data in json format")


class InsertLogResponse(BaseModel):
    hash: Optional[str] = Field(None, description="hash of the inserted data")
    error: Optional[str] = Field(None, description="error message")


@router.post("/insert", response_model=InsertLogResponse)
async def insert(
    request: InsertLogRequest,
):
    # TODO: handle error
    error_msg = None
    prompt = gen_log_prompt(request.jsondata, request.filepath)

    insert_log_prompt(prompt, request.workspace)
    return InsertLogResponse(hash=prompt.hash, error=error_msg)


class DeleteLogRequest(BaseModel):
    hash: str = Field(..., description="hash of the prompt to delete")
    workspace: Optional[str] = Field(None, description="absolute path to the workspace/repository")


class DeleteLogResponse(BaseModel):
    success: bool = Field(..., description="success status")
    error: Optional[str] = Field(None, description="error message")


@router.post("/delete")
async def delete(
    request: DeleteLogRequest,
):
    print(f"\n\ncheck delete log request: \n{request}")

    success, error_msg = delete_log_prompt(request.hash, request.workspace)

    return DeleteLogResponse(success=success, error=error_msg)
