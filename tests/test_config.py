import os
from devchat.config import ConfigManager, ModelConfig, ChatConfig, OpenAIChatConfig


def test_create_sample_config():
    ConfigManager('/tmp')
    assert os.path.exists('/tmp/config.yml')


def test_load_and_validate_config():
    config_manager = ConfigManager('/tmp')
    assert isinstance(config_manager.config, ChatConfig)


def test_get_model_config():
    config_manager = ConfigManager('/tmp')
    model_config = config_manager.get_model_config('gpt-4')
    assert model_config.id == 'gpt-4'
    assert model_config.max_input_tokens == 6000
    assert model_config.parameters.temperature == 0
    assert model_config.parameters.stream is True


def test_update_model_config():
    config_manager = ConfigManager('/tmp')
    new_model_config = ModelConfig(
        id='gpt-4',
        max_input_tokens=7000,
        parameters=OpenAIChatConfig(model="TO_REMOVE", temperature=0.5)
    )
    updated_model_config = config_manager.update_model_config(new_model_config)
    assert updated_model_config.max_input_tokens == 7000
    assert updated_model_config.parameters.temperature == 0.5
    assert updated_model_config.parameters.stream is True
