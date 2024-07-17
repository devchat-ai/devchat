from typing import List, Optional

from pydantic import BaseModel, Field


class UserMessage(BaseModel):
    content: str = Field(..., description="message content")
    model_name: str = Field(..., description="LLM model name")
    workspace: Optional[str] = Field(None, description="absolute path to the workspace/repository")
    api_key: Optional[str] = Field(None, description="API key (OpenAI API key or DevChat Key)")
    api_base: Optional[str] = Field(None, description="API base url")
    parent: Optional[str] = Field(None, description="parent message hash in a thread")
    context: Optional[List[str]] = Field(None, description="paths to context files")


class InsertLog(BaseModel):
    workspace: Optional[str] = Field(None, description="absolute path to the workspace/repository")
    jsondata: Optional[str] = Field(None, description="data to insert in json format")
    filepath: Optional[str] = Field(None, description="file path to insert data in json format")


class DeleteLog(BaseModel):
    hash: str = Field(..., description="hash of the prompt to delete")
    workspace: Optional[str] = Field(None, description="absolute path to the workspace/repository")


class DeleteTopic(BaseModel):
    topic_hash: str = Field(..., description="hash of the topic to delete")
    workspace: Optional[str] = Field(None, description="absolute path to the workspace/repository")
