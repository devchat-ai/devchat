from enum import Enum
import os
import sys
from typing import List, Dict, Tuple, Union, Optional
from pydantic import BaseModel
import oyaml as yaml
from devchat.openai import OpenAIChatParameters
from devchat.anthropic import AnthropicChatParameters


class Client(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GENERAL = "general"


class ProviderConfig(BaseModel):
    client: Optional[str]


class OpenAIProviderConfig(ProviderConfig, extra='forbid'):
    api_key: Optional[str]
    api_base: Optional[str]
    api_type: Optional[str]
    api_version: Optional[str]
    deployment_name: Optional[str]


class AnthropicProviderConfig(ProviderConfig, extra='forbid'):
    api_key: Optional[str]
    api_base: Optional[str]
    timeout: Optional[float]


class ModelConfig(BaseModel, extra='forbid'):
    max_input_tokens: Optional[int] = sys.maxsize
    provider: Optional[str]


class OpenAIModelConfig(ModelConfig, OpenAIChatParameters):
    pass


class AnthropicModelConfig(ModelConfig, AnthropicChatParameters):
    pass


class GeneralModelConfig(ModelConfig):
    max_tokens: Optional[int]
    stop_sequences: Optional[List[str]]
    temperature: Optional[float]
    top_p: Optional[float]
    top_k: Optional[int]
    stream: Optional[bool]


class ChatConfig(BaseModel, extra='forbid'):
    providers: Optional[Dict[str, Union[OpenAIProviderConfig,
                                        AnthropicProviderConfig,
                                        ProviderConfig]]]
    models: Dict[str, Union[OpenAIModelConfig, AnthropicModelConfig, GeneralModelConfig]]
    default_model: Optional[str]


class ConfigManager:
    def __init__(self, dir_path: str):
        self.config_path = os.path.join(dir_path, 'config.yml')
        if not os.path.exists(self.config_path):
            self._create_sample_file()
            self._file_is_new = True
        else:
            self._file_is_new = False
        self.config = self._load_and_validate_config()

    @property
    def file_is_new(self) -> bool:
        return self._file_is_new

    @property
    def file_last_modified(self) -> float:
        return os.path.getmtime(self.config_path)

    def _load_and_validate_config(self) -> ChatConfig:
        with open(self.config_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        if 'providers' in data:
            for provider, config in data['providers'].items():
                if config['client'] == "openai":
                    data['providers'][provider] = OpenAIProviderConfig(**config)
                elif config['client'] == "anthropic":
                    data['providers'][provider] = AnthropicProviderConfig(**config)
                else:
                    data['providers'][provider] = ProviderConfig(**config)
        for model, config in data['models'].items():
            if 'provider' not in config:
                data['models'][model] = GeneralModelConfig(**config)
            elif 'parameters' in config:
                provider = data['providers'][config['provider']]
                if provider.client == Client.OPENAI:
                    data['models'][model] = OpenAIModelConfig(**config)
                elif provider.client == Client.ANTHROPIC:
                    data['models'][model] = AnthropicModelConfig(**config)
                else:
                    data['models'][model] = GeneralModelConfig(**config)

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

    def update_model_config(
        self,
        model_id: str,
        new_config: Union[OpenAIModelConfig, AnthropicModelConfig]
    ) -> Union[OpenAIModelConfig, AnthropicModelConfig]:
        _, old_config = self.model_config(model_id)
        if new_config.max_input_tokens is not None:
            old_config.max_input_tokens = new_config.max_input_tokens
        updated_parameters = old_config.dict(exclude_unset=True)
        updated_parameters.update(new_config.dict(exclude_unset=True))
        self.config.models[model_id] = type(new_config)(**updated_parameters)
        return self.config.models[model_id]

    def sync(self):
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.config.dict(exclude_unset=True), file)

    def _create_sample_file(self):
        sample_config = ChatConfig(
            providers={
                "devchat.ai": OpenAIProviderConfig(
                    client=Client.OPENAI,
                    api_key=""
                ),
                "openai.com": OpenAIProviderConfig(
                    client=Client.OPENAI,
                    api_key=""
                ),
                "general": ProviderConfig(
                    client=Client.GENERAL
                )
            },
            models={
                "gpt-4": OpenAIModelConfig(
                    max_input_tokens=6000,
                    provider='devchat.ai',
                    temperature=0,
                    stream=True
                ),
                "gpt-3.5-turbo-16k": OpenAIModelConfig(
                    max_input_tokens=12000,
                    provider='devchat.ai',
                    temperature=0,
                    stream=True
                ),
                "gpt-3.5-turbo": OpenAIModelConfig(
                    max_input_tokens=3000,
                    provider='devchat.ai',
                    temperature=0,
                    stream=True
                ),
                "claude-2": GeneralModelConfig(
                    provider='general',
                    max_tokens=20000
                )
            },
            default_model="gpt-3.5-turbo"
        )
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(sample_config.dict(exclude_unset=True), file)
