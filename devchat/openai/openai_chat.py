import json
import os
from typing import Dict, Iterator, List, Optional, Union

from pydantic import BaseModel, Field

from devchat.chat import Chat
from devchat.utils import get_user_info, user_id

from .http_openai import stream_request
from .openai_message import OpenAIMessage
from .openai_prompt import OpenAIPrompt


class OpenAIChatParameters(BaseModel, extra="ignore"):
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


class OpenAIChatConfig(OpenAIChatParameters):
    """
    Configuration object for the OpenAIChat APIs.
    """

    model: str


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

    def init_prompt(self, request: str, function_name: Optional[str] = None) -> OpenAIPrompt:
        user, email = get_user_info()
        self.config.user = user_id(user, email)[1]
        prompt = OpenAIPrompt(self.config.model, user, email)
        prompt.set_request(request, function_name=function_name)
        return prompt

    def load_prompt(self, data: dict) -> OpenAIPrompt:
        data["_new_messages"] = {
            k: [OpenAIMessage.from_dict(m) for m in v]
            if isinstance(v, list)
            else OpenAIMessage.from_dict(v)
            for k, v in data["_new_messages"].items()
            if k != "function"
        }
        data["_history_messages"] = {
            k: [OpenAIMessage.from_dict(m) for m in v] for k, v in data["_history_messages"].items()
        }
        return OpenAIPrompt(**data)

    def complete_response(self, prompt: OpenAIPrompt) -> str:
        import httpx
        import openai

        # Filter the config parameters with set values
        config_params = self.config.dict(exclude_unset=True)
        if prompt.get_functions():
            config_params["functions"] = prompt.get_functions()
            config_params["function_call"] = "auto"
        config_params["stream"] = False

        proxy_url = os.environ.get("DEVCHAT_PROXY", "")
        proxy_setting = (
            {"proxy": {"https://": proxy_url, "http://": proxy_url}} if proxy_url else {}
        )

        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", None),
            base_url=os.environ.get("OPENAI_API_BASE", None),
            http_client=httpx.Client(**proxy_setting, trust_env=False),
        )

        response = client.chat.completions.create(messages=prompt.messages, **config_params)
        if isinstance(response, openai.types.chat.chat_completion.ChatCompletion):
            return json.dumps(response.dict())
        return str(response)

    def stream_response(self, prompt: OpenAIPrompt) -> Iterator:
        api_key = os.environ.get("OPENAI_API_KEY", None)
        base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1/")

        if (
            not os.environ.get("USE_TIKTOKEN", False)
            and base_url.find("https://api.openai.com/v1") == -1
        ):
            config_params = self.config.dict(exclude_unset=True)
            if prompt.get_functions():
                config_params["functions"] = prompt.get_functions()
                config_params["function_call"] = "auto"
            config_params["stream"] = True

            data = {"messages": prompt.messages, **config_params, "timeout": 180}
            response = stream_request(api_key, base_url, data)
            return response
        import httpx
        import openai

        # Filter the config parameters with set values
        config_params = self.config.dict(exclude_unset=True)
        if prompt.get_functions():
            config_params["functions"] = prompt.get_functions()
            config_params["function_call"] = "auto"
        config_params["stream"] = True

        proxy_url = os.environ.get("DEVCHAT_PROXY", "")
        proxy_setting = (
            {"proxy": {"https://": proxy_url, "http://": proxy_url}} if proxy_url else {}
        )

        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", None),
            base_url=os.environ.get("OPENAI_API_BASE", None),
            http_client=httpx.Client(**proxy_setting, trust_env=False),
        )

        response = client.chat.completions.create(
            messages=prompt.messages, **config_params, timeout=180
        )
        return response
