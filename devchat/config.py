from enum import Enum
import os
import sys
from typing import Dict, List, Union, Optional
from pydantic import BaseModel, validator
import yaml
from devchat.openai import OpenAIChatParameters
from devchat.anthropic import AnthropicChatParameters


class Client(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class OpenAIClientConfig(BaseModel, extra='forbid'):
    api_key: str
    api_base: Optional[str]
    api_type: Optional[str]
    api_version: Optional[str]
    deployment_name: Optional[str]


class AnthropicClientConfig(BaseModel, extra='forbid'):
    api_key: str
    api_base: Optional[str]
    timeout: Optional[float]


class ProviderConfig(BaseModel, extra='forbid', use_enum_values=True):
    client: Client
    client_config: Union[OpenAIClientConfig, AnthropicClientConfig]

    @validator('client_config', pre=True)
    def create_client_config(cls, config, values):  # pylint: disable=E0213
        if not isinstance(config, dict):
            return config
        if 'client' in values:
            if values['client'] == Client.OPENAI:
                return OpenAIClientConfig(**config)
            if values['client'] == Client.ANTHROPIC:
                return AnthropicClientConfig(**config)
        raise ValueError(f"Invalid client in {values}")


class ModelConfig(BaseModel, extra='forbid'):
    id: str
    max_input_tokens: Optional[int] = sys.maxsize
    parameters: Optional[Union[OpenAIChatParameters, AnthropicChatParameters]]
    provider: Optional[str]


class ChatConfig(BaseModel, extra='forbid'):
    providers: Dict[str, ProviderConfig]
    models: List[ModelConfig]
    default_model: Optional[str]


class ConfigManager:
    def __init__(self, dir_path: str):
        self.config_path = os.path.join(dir_path, 'config.yml')
        if not os.path.exists(self.config_path):
            self._create_sample_config()
        self.config = self._load_and_validate_config()

    def _load_and_validate_config(self) -> ChatConfig:
        with open(self.config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        for provider, config in config_data['providers'].items():
            config_data['providers'][provider] = ProviderConfig(**config)
        for model in config_data['models']:
            if 'provider' not in model:
                raise ValueError(f"Model in {self.config_path} is missing provider")
            if 'parameters' in model:
                provider_config = config_data['providers'][model['provider']]
                if provider_config.client == Client.OPENAI:
                    model['parameters'] = OpenAIChatParameters(**model['parameters'])
                elif provider_config.client == Client.ANTHROPIC:
                    model['parameters'] = AnthropicChatParameters(**model['parameters'])
                else:
                    raise ValueError(f"Model in {self.config_path} has invalid client: "
                                     f"{provider_config.client}")
        return ChatConfig(**config_data)

    def model_config(self, model_id: Optional[str] = None) -> ModelConfig:
        if not model_id:
            if not self.config.models:
                raise ValueError(f"No models found in {self.config_path}")
            if self.config.default_model:
                return self.model_config(self.config.default_model)
            return self.config.models[0]
        for model in self.config.models:
            if model.id == model_id:
                return model
        raise ValueError(f"Model {model_id} not found in {self.config_path}")

    def provider_config(self, provider_id: str) -> ProviderConfig:
        for provider in self.config.providers:
            if provider.id == provider_id:
                return provider
        raise ValueError(f"Provider {provider_id} not found in {self.config_path}")

    def update_model_config(self, model_config: ModelConfig) -> ModelConfig:
        model = self.model_config(model_config.id)
        if not model:
            return None
        if model_config.max_input_tokens is not None:
            model.max_input_tokens = model_config.max_input_tokens
        if model_config.parameters is not None:
            updated_parameters = model.parameters.dict(exclude_unset=True)
            updated_parameters.update(model_config.parameters.dict(exclude_unset=True))
            model.parameters = OpenAIChatParameters(**updated_parameters)
        return model

    def sync(self):
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.config.dict(exclude_unset=True), file)

    def _create_sample_config(self):
        sample_config = ChatConfig(
            providers={
                "devchat": ProviderConfig(
                    client=Client.OPENAI,
                    client_config=OpenAIClientConfig(api_key="DC....SET.THIS")
                ),
                "openai": ProviderConfig(
                    client=Client.OPENAI,
                    client_config=OpenAIClientConfig(api_key="sk-...SET-THIS")
                ),
                "azure-openai": ProviderConfig(
                    client=Client.OPENAI,
                    client_config=OpenAIClientConfig(
                        api_key="YOUR_AZURE_OPENAI_KEY",
                        api_base="YOUR_AZURE_OPENAI_ENDPOINT",
                        api_version='2023-05-15',
                        deployment_name='YOUR_AZURE_DEPLOYMENT_NAME'
                    )
                ),
                "anthropic": ProviderConfig(
                    client=Client.ANTHROPIC,
                    client_config=AnthropicClientConfig(api_key="sk-ant-...SET-THIS", timeout=30)
                )
            },
            models=[
                ModelConfig(
                    id="gpt-4",
                    max_input_tokens=6000,
                    parameters=OpenAIChatParameters(temperature=0, stream=True),
                    provider='devchat'
                ),
                ModelConfig(
                    id="gpt-3.5-turbo-16k",
                    max_input_tokens=12000,
                    parameters=OpenAIChatParameters(temperature=0, stream=True),
                    provider='devchat'
                ),
                ModelConfig(
                    id="gpt-3.5-turbo",
                    max_input_tokens=3000,
                    parameters=OpenAIChatParameters(temperature=0, stream=True),
                    provider='devchat'
                ),
                ModelConfig(
                    id="claude-2",
                    parameters=AnthropicChatParameters(max_tokens_to_sample=20000),
                    provider='anthropic'
                )
            ]
        )
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(sample_config.dict(exclude_unset=True), file)
