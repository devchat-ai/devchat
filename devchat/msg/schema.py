from typing import Dict, Optional, List, Iterator

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    content: str = Field(..., description="message content")
    model_name: str = Field(..., description="LLM model name")
    parent: Optional[str] = Field(None, description="parent message hash in a thread")
    context: Optional[List[str]] = Field(None, description="paths to context files")


class MessageResponseChunk(BaseModel):
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
