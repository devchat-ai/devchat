from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MessageCompletionChunk(BaseModel):
    # TODO: add response hash
    # response_hash: str = Field(
    #     ...,
    #     description="response hash, all chunks in a response should have the same hash",
    # )
    user: str = Field(..., description="user info")
    date: str = Field(..., description="date time")
    content: str = Field(..., description="chunk content")
    finish_reason: str = Field(default="", description="finish reason")
    # TODO: should handle isError in another way?
    isError: bool = Field(default=False, description="is error")
    extra: Dict = Field(default_factory=dict, description="extra data")


class InsertLog(BaseModel):
    hash: Optional[str] = Field(None, description="hash of the inserted data")


class DeleteLog(BaseModel):
    success: bool = Field(..., description="success status")


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


class TopicSummary(BaseModel):
    latest_time: int = Field(..., description="timestamp of the latest log")
    hidden: bool = Field(..., description="hidden status of the topic")
    # root prompt info
    root_prompt_hash: str = Field(..., description="hash of the log summary")
    root_prompt_user: str = Field(..., description="root hash of the log")
    root_prompt_date: int = Field(..., description="timestamp")
    root_prompt_request: str = Field(..., description="truncated request content(message)")
    root_prompt_response: str = Field(..., description="truncated response content(message)")
    title: Optional[str] = Field(None, description="title of the topic")


class DeleteTopic(BaseModel):
    topic_hash: str = Field(..., description="hash of the deleted topic")


class UpdateWorkflows(BaseModel):
    updated: bool = Field(..., description="Whether the workflows are updated.")
    message: str = Field(..., description="The message of the update.")
