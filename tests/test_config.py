import os
from devchat.config import ConfigManager, ModelConfig, ChatConfig, OpenAIChatParameters


def test_create_sample_config(tmp_path):
    ConfigManager(tmp_path)
    assert os.path.exists(os.path.join(tmp_path, 'config.yml'))


def test_load_and_validate_config(tmp_path):
    config_manager = ConfigManager(tmp_path)
    assert isinstance(config_manager.config, ChatConfig)


def test_get_model_config(tmp_path):
    config_manager = ConfigManager(tmp_path)
    model_config = config_manager.model_config('gpt-4')
    assert model_config.id == 'gpt-4'
    assert model_config.max_input_tokens == 6000
    assert model_config.parameters.temperature == 0
    assert model_config.parameters.stream is True


def test_update_model_config(tmp_path):
    config_manager = ConfigManager(tmp_path)
    new_model_config = ModelConfig(
        id='gpt-4',
        max_input_tokens=7000,
        parameters=OpenAIChatParameters(temperature=0.5)
    )
    updated_model_config = config_manager.update_model_config(new_model_config)
    assert updated_model_config == config_manager.model_config('gpt-4')
    assert updated_model_config.max_input_tokens == 7000
    assert updated_model_config.parameters.temperature == 0.5
    assert updated_model_config.parameters.stream is True

    config_manager.sync()
    fresh_config_manager = ConfigManager(tmp_path)
    assert config_manager.config == fresh_config_manager.config
