import os
from typing import List, Optional
from pydantic import BaseModel
import yaml
from devchat.openai import OpenAIChatParameters


class ModelConfig(BaseModel):
    id: str
    max_input_tokens: Optional[int]
    parameters: Optional[OpenAIChatParameters]


class ChatConfig(BaseModel):
    models: Optional[List[ModelConfig]]


class ConfigManager:
    def __init__(self, dir_path: str):
        self.config_path = os.path.join(dir_path, 'config.yml')
        if not os.path.exists(self.config_path):
            self._create_sample_config()
        self.config = self._load_and_validate_config()

    def _create_sample_config(self):
        sample_config = ChatConfig(models=[
            ModelConfig(
                id="gpt-4",
                max_input_tokens=6000,
                parameters=OpenAIChatParameters(temperature=0, stream=True)
            ),
            ModelConfig(
                id="gpt-3.5-turbo-16k",
                max_input_tokens=12000,
                parameters=OpenAIChatParameters(temperature=0, stream=True)
            ),
            ModelConfig(
                id="gpt-3.5-turbo",
                max_input_tokens=3000,
                parameters=OpenAIChatParameters(temperature=0, stream=True)
            )
        ])
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(sample_config.dict(), file)

    def _load_and_validate_config(self) -> ChatConfig:
        with open(self.config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        return ChatConfig(**config_data)

    def get_model_config(self, model_id: Optional[str] = None) -> ModelConfig:
        if not model_id:
            if len(self.config.models) > 0:
                return self.config.models[0]
            return None
        for model in self.config.models:
            if model.id == model_id:
                return model
        return None

    def update_model_config(self, model_config: ModelConfig) -> ModelConfig:
        model = self.get_model_config(model_config.id)
        if not model:
            return None
        if model_config.max_input_tokens is not None:
            model.max_input_tokens = model_config.max_input_tokens
        if model_config.parameters is not None:
            updated_parameters = model.parameters.dict()
            updated_parameters.update(
                {k: v for k, v in model_config.parameters.dict().items() if v is not None})
            model.parameters = OpenAIChatParameters(**updated_parameters)
        return model
