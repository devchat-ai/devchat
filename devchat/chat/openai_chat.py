from typing import Optional, Union, List, Dict
from pydantic import BaseModel, Field
from devchat.message import Message
from devchat.chat import Chat

class OpenAIChatConfig(BaseModel):
    """
    Configuration object for the OpenAIChat class.
    """
    model: str
    temperature: Optional[float] = Field(1, ge=0, le=2)
    top_p: Optional[float] = Field(1, ge=0, le=1)
    num_choices: Optional[int] = Field(1, ge=1)
    stream: Optional[bool] = Field(False)
    stop: Optional[Union[str, List[str]]] = Field(None)
    max_tokens: Optional[int] = Field(None, ge=1)
    presence_penalty: Optional[float] = Field(0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[int, float]] = Field(None)
    user: Optional[str] = Field(None)

class OpenAIChat(Chat):
    """
    OpenAIChat class that handles communication with the OpenAI Chat API.
    """
    def __init__(self, config: OpenAIChatConfig):
        """
        Initialize the OpenAIChat class with a configuration object.

        Args:
            config (OpenAIChatConfig): Configuration object with parameters for the OpenAI Chat API.
        """
        self.config = config

    def prompt(self, messages: List[Message]) -> None:
        """
        Prompt the chat system with a list of Message objects.

        Args:
            messages (List[Message]): A list of messages representing the conversation so far.
        """

    def complete_response(self) -> str:
        """
        Retrieve a complete response JSON string from the chat system.

        Returns:
            str: A JSON string representing the complete response.
        """

    def stream_response(self) -> str:
        """
        Retrieve a streamed response from the chat system.

        Returns:
            str: An iterator of JSON strings representing the streamed response.
        """
