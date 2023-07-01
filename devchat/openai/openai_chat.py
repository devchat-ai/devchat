from typing import Optional, Union, List, Dict, Iterator
from pydantic import BaseModel, Field, Extra
import openai
from devchat.chat import Chat
from devchat.utils import get_user_info, user_id
from .openai_message import OpenAIMessage
from .openai_prompt import OpenAIPrompt


class OpenAIChatConfig(BaseModel):
    """
    Configuration object for the OpenAIChat class.
    """
    model: str
    temperature: Optional[float] = Field(0, ge=0, le=2)
    top_p: Optional[float] = Field(None, ge=0, le=1)
    n: Optional[int] = Field(None, ge=1)
    stream: Optional[bool] = Field(None)
    stop: Optional[Union[str, List[str]]] = Field(None)
    max_tokens: Optional[int] = Field(None, ge=1)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[int, float]] = Field(None)
    user: Optional[str] = Field(None)
    request_timeout: Optional[int] = Field(32, ge=3)

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

    def init_prompt(self, request: str) -> OpenAIPrompt:
        user, email = get_user_info()
        self.config.user = user_id(user, email)[1]
        prompt = OpenAIPrompt(self.config.model, user, email)
        prompt.set_request(request)
        return prompt

    def load_prompt(self, data: dict) -> OpenAIPrompt:
        data['_new_messages'] = {
            k: [OpenAIMessage(**m) for m in v] if isinstance(v, list) else OpenAIMessage(**v)
            for k, v in data['_new_messages'].items()
        }
        data['_history_messages'] = {k: [OpenAIMessage(**m) for m in v]
                                     for k, v in data['_history_messages'].items()}
        return OpenAIPrompt(**data)

    def complete_response(self, prompt: OpenAIPrompt) -> str:
        # Filter the config parameters with non-None values
        config_params = {
            key: value
            for key, value in self.config.dict().items() if value is not None
        }
        config_params['stream'] = False

        response = openai.ChatCompletion.create(
            messages=prompt.messages,
            **config_params
        )
        return response

    def stream_response(self, prompt: OpenAIPrompt) -> Iterator[str]:
        # Filter the config parameters with non-None values
        config_params = {
            key: value
            for key, value in self.config.dict().items() if value is not None
        }
        config_params['stream'] = True

        response = openai.ChatCompletion.create(
            messages=prompt.messages,
            **config_params
        )
        return response
