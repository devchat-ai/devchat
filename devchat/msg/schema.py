from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    content: str = Field(..., description="message content")
    model_name: str = Field(..., description="LLM model name")
    workspace: Optional[str] = Field(None, description="absolute path to the workspace/repository")
    api_key: Optional[str] = Field(None, description="API key (OpenAI API key or DevChat Key)")
    api_base: Optional[str] = Field(None, description="API base url")
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
