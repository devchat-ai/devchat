import os
import json
import shutil
import tempfile
from click.testing import CliRunner
from devchat._cli import main

runner = CliRunner()


def test_main_no_args():
    result = runner.invoke(main)
    assert result.exit_code == 1


def test_main_with_content():
    content = "What is the capital of France? Answer in one word without a period."
    result = runner.invoke(main, [content])
    assert result.exit_code == 0
    assert result.output == "Paris\n"


def test_main_with_temp_config_file():
    config_data = {
        'llm': 'OpenAI',
        'OpenAI': {
            'model': 'gpt-3.5-turbo',
            'temperature': 0.2
        }
    }

    temp_dir = tempfile.mkdtemp()
    temp_config_path = os.path.join(temp_dir, ".chatconfig.json")

    with open(temp_config_path, "w") as temp_config_file:
        json.dump(config_data, temp_config_file)

    original_cwd = os.getcwd()
    os.chdir(temp_dir)

    content = "What is the capital of Spain? Answer in one word without a period."
    result = runner.invoke(main, [content])
    assert result.exit_code == 0
    assert result.output == "Madrid\n"

    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)
