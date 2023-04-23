from typing import Optional, Union, List, Dict, Iterator
from pydantic import BaseModel, Field, Extra
import openai
from devchat.message import Message
from devchat.chat import Chat


class OpenAIChatConfig(BaseModel):
    """
    Configuration object for the OpenAIChat class.
    """
    model: str
    temperature: Optional[float] = Field(None, ge=0, le=2)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    n: Optional[int] = Field(None, ge=1)
    stream: Optional[bool] = Field(None)
    stop: Optional[Union[str, List[str]]] = Field(None)
    max_tokens: Optional[int] = Field(None, ge=1)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[int, float]] = Field(None)
    user: Optional[str] = Field(None)

    class Config:
        """
        Configuration class to forbid extra fields in the model.
        """
        extra = Extra.forbid


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
        self._messages = []

    def prompt(self, messages: List[Message]) -> None:
        """
        Prompt the chat system with a list of Message objects.

        Args:
            messages (List[Message]): A list of messages representing the conversation so far.
        """
        self._messages = [msg.to_dict() for msg in messages]

    def complete_response(self) -> str:
        """
        Retrieve a complete response JSON string from the chat system.

        Returns:
            str: A JSON string representing the complete response.
        """
        # Filter the config parameters with non-None values
        config_params = {
            key: value
            for key, value in self.config.dict().items()
            if value is not None
        }

        # Update the 'stream' parameter to False for complete_response
        config_params = config_params.copy()
        config_params['stream'] = False

        response = openai.ChatCompletion.create(
            messages=self._messages,
            **config_params
        )
        return response

    def stream_response(self) -> Iterator[str]:
        """
        Retrieve a streaming response from the chat system.

        Returns:
            str: An iterator of JSON strings representing the streaming response.
        """
        # Filter the config parameters with non-None values
        config_params = {
            key: value
            for key, value in self.config.dict().items()
            if value is not None
        }

        # Update the 'stream' parameter to True for stream_response
        config_params = config_params.copy()
        config_params['stream'] = True

        response = openai.ChatCompletion.create(
            messages=self._messages,
            **config_params
        )
        return response
