import os
import sys
from typing import Dict, List, Optional, Tuple

import oyaml as yaml
from pydantic import BaseModel


class GeneralProviderConfig(BaseModel):
    api_key: Optional[str]
    api_base: Optional[str]


class ModelConfig(BaseModel):
    max_input_tokens: Optional[int] = sys.maxsize
    provider: Optional[str]


class GeneralModelConfig(ModelConfig):
    max_tokens: Optional[int]
    stop_sequences: Optional[List[str]]
    temperature: Optional[float]
    top_p: Optional[float]
    top_k: Optional[int]
    stream: Optional[bool]


class ChatConfig(BaseModel):
    providers: Optional[Dict[str, GeneralProviderConfig]]
    models: Dict[str, GeneralModelConfig]
    default_model: Optional[str]


class ConfigManager:
    def __init__(self, dir_path: str):
        self.config_path = os.path.join(dir_path, "config.yml")
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
        with open(self.config_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if "providers" in data:
            for provider, config in data["providers"].items():
                data["providers"][provider] = GeneralProviderConfig(**config)
        for model, config in data["models"].items():
            data["models"][model] = GeneralModelConfig(**config)

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
        self, model_id: str, new_config: GeneralModelConfig
    ) -> GeneralModelConfig:
        _, old_config = self.model_config(model_id)
        if new_config.max_input_tokens is not None:
            old_config.max_input_tokens = new_config.max_input_tokens
        updated_parameters = old_config.dict(exclude_unset=True)
        updated_parameters.update(new_config.dict(exclude_unset=True))
        self.config.models[model_id] = type(new_config)(**updated_parameters)
        return self.config.models[model_id]

    def sync(self):
        with open(self.config_path, "w", encoding="utf-8") as file:
            yaml.dump(self.config.dict(exclude_unset=True), file)

    def _create_sample_file(self):
        sample_config = ChatConfig(
            providers={
                "devchat.ai": GeneralProviderConfig(api_key=""),
                "openai.com": GeneralProviderConfig(api_key=""),
                "general": GeneralProviderConfig(),
            },
            models={
                "gpt-4": GeneralModelConfig(
                    max_input_tokens=6000, provider="devchat.ai", temperature=0, stream=True
                ),
                "gpt-3.5-turbo-16k": GeneralModelConfig(
                    max_input_tokens=12000, provider="devchat.ai", temperature=0, stream=True
                ),
                "gpt-3.5-turbo": GeneralModelConfig(
                    max_input_tokens=3000, provider="devchat.ai", temperature=0, stream=True
                ),
                "claude-2": GeneralModelConfig(provider="general", max_tokens=20000),
            },
            default_model="gpt-3.5-turbo",
        )
        with open(self.config_path, "w", encoding="utf-8") as file:
            yaml.dump(sample_config.dict(exclude_unset=True), file)
