import os
from click.testing import CliRunner
from devchat.config import ConfigManager, OpenAIModelConfig, ChatConfig
from devchat._cli.main import main

runner = CliRunner()


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
    assert config.temperature == 0
    assert config.stream is True


def test_update_model_config(tmp_path):
    model = 'gpt-4'
    config_manager = ConfigManager(tmp_path)
    config = OpenAIModelConfig(
        max_input_tokens=7000,
        temperature=0.5
    )
    updated_model_config = config_manager.update_model_config(model, config)
    assert updated_model_config == config_manager.model_config(model)[1]
    assert updated_model_config.max_input_tokens == 7000
    assert updated_model_config.temperature == 0.5
    assert updated_model_config.stream is True

    config_manager.sync()
    fresh_config_manager = ConfigManager(tmp_path)
    assert config_manager.config == fresh_config_manager.config


def test_legacy_config(git_repo, mock_home_dir):
    repo_chat_dir = os.path.join(git_repo, ".chat")
    os.makedirs(repo_chat_dir)
    home_chat_dir = os.path.join(mock_home_dir, ".chat")

    legacy_config = '''
    {
        "model": "gpt-3.5-turbo",
        "provider": "OpenAI",
        "tokens-per-prompt": 2000,
        "OpenAI": {
            "temperature": 0.2
        }
    }
    '''

    legacy_file = os.path.join(repo_chat_dir, "config.json")
    with open(legacy_file, 'w', encoding='utf-8') as file:
        file.write(legacy_config)

    result = runner.invoke(main, ['log'])
    assert result.exit_code == 0
    assert not os.path.exists(legacy_file)
    assert os.path.isfile(legacy_file + '.old')
    config_manager = ConfigManager(home_chat_dir)
    assert config_manager.config.default_model == 'gpt-3.5-turbo'
    assert config_manager.config.models['gpt-3.5-turbo'].max_input_tokens == 2000
    assert config_manager.config.models['gpt-3.5-turbo'].temperature == 0.2
    assert config_manager.config.models['gpt-3.5-turbo'].stream is True

    legacy_config = '''
    {
        "model": "gpt-3.5-turbo",
        "provider": "OpenAI",
        "tokens-per-prompt": 2000,
        "OpenAI": {
            "stream": false
        }
    }
    '''
    with open(legacy_file, 'w', encoding='utf-8') as file:
        file.write(legacy_config)

    result = runner.invoke(main, ['prompt', "This is a test. Reply nothing."])
    assert result.exit_code == 0
    config_manager = ConfigManager(home_chat_dir)
    assert config_manager.config.default_model == 'gpt-3.5-turbo'
    assert config_manager.config.models['gpt-3.5-turbo'].max_input_tokens == 2000
    assert config_manager.config.models['gpt-3.5-turbo'].temperature == 0.2
    assert config_manager.config.models['gpt-3.5-turbo'].stream is False
