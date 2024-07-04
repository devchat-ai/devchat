import time
import json

from typing import Dict, Optional, List, Iterator
from fastapi import APIRouter, Query

from pydantic import BaseModel, Field
from devchat.msg.logm import get_topic_shortlogs, get_topics, delete_topic as del_topic
from pprint import pprint

router = APIRouter()


@router.get("/hello")
async def hello():
    return {"hello": "devchat topic"}


class ShortLog(BaseModel):
    user: str = Field(..., description="user id (name and email)")
    date: int = Field(..., description="timestamp")
    context: List[Dict] = Field(..., description="context data")
    request: str = Field(..., description="request content(message)")
    responses: List[str] = Field(..., description="response contents(messages)")
    request_tokens: int = Field(..., description="number of tokens in the request")
    response_tokens: int = Field(..., description="number of tokens in the response")
    hash: str = Field(..., description="hash of the log record")
    parent: Optional[str] = Field(None, description="hash of the parent log record")


@router.get("/{topic_root_hash}/logs", response_model=List[ShortLog])
async def get_topic_logs(
    topic_root_hash: str,
    limit: int = Query(1, gt=0, description="maximum number of records to return"),
    offset: int = Query(0, ge=0, description="offset of the first record to return"),
    workspace: Optional[str] = Query(
        None, description="absolute path to the workspace/repository"
    ),
):
    # TODO: handle error in the http way
    records, error = get_topic_shortlogs(topic_root_hash, limit, offset, workspace)

    logs = [ShortLog.parse_obj(record) for record in records]
    return logs


class TopicSummary(BaseModel):
    latest_time: int = Field(..., description="timestamp of the latest log")
    hidden: bool = Field(..., description="hidden status of the topic")
    # root prompt info
    root_prompt_hash: str = Field(..., description="hash of the log summary")
    root_prompt_user: str = Field(..., description="root hash of the log")
    root_prompt_date: int = Field(..., description="timestamp")
    root_prompt_request: str = Field(
        ..., description="truncated request content(message)"
    )
    root_prompt_response: str = Field(
        ..., description="truncated response content(message)"
    )
    title: Optional[str] = Field(None, description="title of the topic")


@router.get("", response_model=List[TopicSummary])
def list_topics(
    limit: int = Query(1, gt=0, description="maximum number of records to return"),
    offset: int = Query(0, ge=0, description="offset of the first record to return"),
    workspace: Optional[str] = Query(
        None, description="absolute path to the workspace/repository"
    ),
):
    topics = get_topics(
        limit=limit, offset=offset, workspace_path=workspace, with_deleted=False
    )

    summaries = [
        TopicSummary(
            latest_time=topic["latest_time"],
            title=topic["title"],
            hidden=topic["hidden"],
            root_prompt_hash=topic["root_prompt"]["hash"],
            root_prompt_user=topic["root_prompt"]["user"],
            root_prompt_date=topic["root_prompt"]["date"],
            root_prompt_request=topic["root_prompt"]["request"],
            root_prompt_response=topic["root_prompt"]["responses"][0],
        )
        for topic in topics
    ]
    return summaries


class DeleteTopicResquest(BaseModel):
    topic_hash: str = Field(..., description="hash of the topic to delete")
    workspace: Optional[str] = Field(
        None, description="absolute path to the workspace/repository"
    )


class DeleteTopicResponse(BaseModel):
    topic_hash: str = Field(..., description="hash of the deleted topic")
    success: bool = Field(..., description="success status")
    error: Optional[str] = Field(None, description="error message")


@router.post("/delete", response_model=DeleteTopicResponse)
def delete_topic(
    request: DeleteTopicResquest,
):
    print(f"check delete topic request: \n{request}")
    try:
        del_topic(request.topic_hash, request.workspace)
        return DeleteTopicResponse(topic_hash=request.topic_hash, success=True)
    except Exception as e:
        return DeleteTopicResponse(
            topic_hash=request.topic_hash, success=False, error=str(e)
        )
