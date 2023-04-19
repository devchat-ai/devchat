import json
import tempfile
from click.testing import CliRunner
from devchat._cli import main

def test_main_openai():
    config_data = {
        "llm": "OpenAI",
        "OpenAI": {
            "model": "text-davinci-002",
            "temperature": 0.8,
            "num_choices": 1,
        }
    }

    with tempfile.NamedTemporaryFile('w+', encoding='utf-8', delete=False) as config_file:
        json.dump(config_data, config_file)
        config_file.flush()

        runner = CliRunner()
        result = runner.invoke(main, [config_file.name])

        assert result.exit_code == 0
        expected_output = (
            "Config: model='text-davinci-002' temperature=0.8 top_p=1 num_choices=1 "
            "stream=False stop=None max_tokens=None presence_penalty=0 "
            "frequency_penalty=0 logit_bias=None user=None"
        )
        assert expected_output in result.output

def test_main_unknown_llm():
    config_data = {
        "llm": "UnknownLLM",
    }

    with tempfile.NamedTemporaryFile('w+', encoding='utf-8', delete=False) as config_file:
        json.dump(config_data, config_file)
        config_file.flush()

        runner = CliRunner()
        result = runner.invoke(main, [config_file.name])

        assert result.exit_code == 0
        assert "Unknown LLM: UnknownLLM" in result.output
