import time
import json
from concurrent.futures import ProcessPoolExecutor

from typing import Dict, Optional, List, Iterator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from pydantic import BaseModel, Field

from devchat.msg.logm import gen_log_prompt, insert_log_promt

router = APIRouter()


@router.get("/hello")
async def hello():
    return {"hello": "devchat log"}


class InsertLogRequest(BaseModel):
    jsondata: Optional[str] = Field(None, description="data to insert in json format")
    filepath: Optional[str] = Field(None, description="file path to insert data in json format")

class InsertLogResponse(BaseModel):
    hash: Optional[str] = Field(None, description="hash of the inserted data")
    error: Optional[str] = Field(None, description="error message")

@router.post("/insert", response_model=InsertLogResponse)
async def insert(
    request: InsertLogRequest,
):
    print(f"\n\ncheck insert log request: \n{request}")
    # TODO: handle error
    error_msg = None
    prompt = gen_log_prompt(request.jsondata, request.filepath)

    insert_log_promt(prompt)
    # # execute the insert in a separate process?
    # with ProcessPoolExecutor() as executor:
    #     executor.submit(insert_log_promt, prompt)

    return InsertLogResponse(hash=prompt.hash, error=error_msg)



