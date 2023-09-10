from enum import Enum
import os
import sys
from typing import Dict, Tuple, Union, Optional
from pydantic import BaseModel
import yaml
from devchat.openai import OpenAIChatParameters
from devchat.anthropic import AnthropicChatParameters


class Client(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ProviderConfig(BaseModel, use_enum_values=True):
    client: Client


class OpenAIProviderConfig(ProviderConfig, extra='forbid'):
    api_key: str
    api_base: Optional[str]
    api_type: Optional[str]
    api_version: Optional[str]
    deployment_name: Optional[str]


class AnthropicProviderConfig(ProviderConfig, extra='forbid'):
    api_key: str
    api_base: Optional[str]
    timeout: Optional[float]


class ModelConfig(BaseModel, extra='forbid'):
    max_input_tokens: Optional[int] = sys.maxsize
    parameters: Optional[Union[OpenAIChatParameters, AnthropicChatParameters]]
    provider: Optional[str]


class ChatConfig(BaseModel, extra='forbid'):
    providers: Dict[str, ProviderConfig]
    models: Dict[str, ModelConfig]
    default_model: Optional[str]


class ConfigManager:
    def __init__(self, dir_path: str):
        self.config_path = os.path.join(dir_path, 'config.yml')
        if not os.path.exists(self.config_path):
            self._create_sample_config()
        self.config = self._load_and_validate_config()

    def _load_and_validate_config(self) -> ChatConfig:
        with open(self.config_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        for provider, config in data['providers'].items():
            if config['client'] == Client.OPENAI:
                data['providers'][provider] = OpenAIProviderConfig(**config)
            elif config['client'] == Client.ANTHROPIC:
                data['providers'][provider] = AnthropicProviderConfig(**config)
            else:
                raise ValueError(f"Provider '{provider}' in {self.config_path} has invalid client: "
                                 f"{config.client}")
        for model, config in data['models'].items():
            if 'provider' not in config:
                raise ValueError(f"Model '{model}' in {self.config_path} is missing provider")
            if 'parameters' in config:
                provider = data['providers'][config['provider']]
                if provider.client == Client.OPENAI:
                    config['parameters'] = OpenAIChatParameters(**config['parameters'])
                elif provider.client == Client.ANTHROPIC:
                    config['parameters'] = AnthropicChatParameters(**config['parameters'])
                else:
                    raise ValueError(f"Model '{model}' in {self.config_path} has invalid provider")
        return ChatConfig(**data)

    def model_config(self, model_id: Optional[str] = None) -> Tuple[str, ModelConfig]:
        if not model_id:
            if self.config.default_model:
                return self.model_config(self.config.default_model)
            if self.config.models:
                return next(iter(self.config.models.items()))
            raise ValueError(f"No models found in {self.config_path}")
        if model_id not in self.config.models:
            raise ValueError(f"Model '{model_id}' not found in {self.config_path}")
        return model_id, self.config.models[model_id]

    def update_model_config(self, model_id: str, new_config: ModelConfig) -> ModelConfig:
        _, old_config = self.model_config(model_id)
        if new_config.max_input_tokens is not None:
            old_config.max_input_tokens = new_config.max_input_tokens
        if new_config.parameters is not None:
            updated_parameters = old_config.parameters.dict(exclude_unset=True)
            updated_parameters.update(new_config.parameters.dict(exclude_unset=True))
            old_config.parameters = type(new_config.parameters)(**updated_parameters)
        return old_config

    def sync(self):
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.config.dict(exclude_unset=True), file)

    def _create_sample_config(self):
        sample_config = ChatConfig(
            providers={
                "devchat.ai": OpenAIProviderConfig(
                    client=Client.OPENAI,
                    api_key="DC....SET.THIS"
                ),
                "openai.com": OpenAIProviderConfig(
                    client=Client.OPENAI,
                    api_key="sk-...SET-THIS"
                ),
                "openai.azure.com": OpenAIProviderConfig(
                    client=Client.OPENAI,
                    api_key="YOUR_AZURE_OPENAI_KEY",
                    api_base="YOUR_AZURE_OPENAI_ENDPOINT",
                    api_version='2023-05-15',
                    deployment_name='YOUR_AZURE_DEPLOYMENT_NAME'
                ),
                "anthropic.com": AnthropicProviderConfig(
                    client=Client.ANTHROPIC,
                    api_key="sk-ant-...SET-THIS",
                    timeout=30
                )
            },
            models={
                "gpt-4": ModelConfig(
                    max_input_tokens=6000,
                    parameters=OpenAIChatParameters(temperature=0, stream=True),
                    provider='devchat.ai'
                ),
                "gpt-3.5-turbo-16k": ModelConfig(
                    max_input_tokens=12000,
                    parameters=OpenAIChatParameters(temperature=0, stream=True),
                    provider='devchat.ai'
                ),
                "gpt-3.5-turbo": ModelConfig(
                    max_input_tokens=3000,
                    parameters=OpenAIChatParameters(temperature=0, stream=True),
                    provider='devchat.ai'
                ),
                "claude-2": ModelConfig(
                    parameters=AnthropicChatParameters(max_tokens_to_sample=20000),
                    provider='anthropic.com'
                )
            },
            default_model="gpt-3.5-turbo"
        )
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(sample_config.dict(exclude_unset=True), file)
