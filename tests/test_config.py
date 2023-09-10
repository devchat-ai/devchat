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
    _, config = config_manager.model_config('gpt-4')
    assert config.max_input_tokens == 6000
    assert config.parameters.temperature == 0
    assert config.parameters.stream is True


def test_update_model_config(tmp_path):
    model = 'gpt-4'
    config_manager = ConfigManager(tmp_path)
    config = ModelConfig(
        max_input_tokens=7000,
        parameters=OpenAIChatParameters(temperature=0.5)
    )
    updated_model_config = config_manager.update_model_config(model, config)
    assert updated_model_config == config_manager.model_config(model)[1]
    assert updated_model_config.max_input_tokens == 7000
    assert updated_model_config.parameters.temperature == 0.5
    assert updated_model_config.parameters.stream is True

    config_manager.sync()
    fresh_config_manager = ConfigManager(tmp_path)
    assert config_manager.config == fresh_config_manager.config
