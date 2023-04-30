import os
import re
import json
import shutil
import tempfile
import pytest
from click.testing import CliRunner
from devchat._cli import main

runner = CliRunner()


def test_main_no_args():
    result = runner.invoke(main, ['prompt'])
    assert result.exit_code == 0


def _check_output_format(output) -> bool:
    pattern = r"(User: .+ <.+@.+>\nDate: .+\n\n(?:.*\n)*\n(?:prompt [a-f0-9]{40}\n\n?)+)"
    return bool(re.fullmatch(pattern, output))


def _get_core_content(output) -> str:
    header_pattern = r"User: .+ <.+@.+>\nDate: .+\n\n"
    footer_pattern = r"\n(?:prompt [a-f0-9]{40}\n\n?)+"

    core_content = re.sub(header_pattern, "", output)
    core_content = re.sub(footer_pattern, "", core_content)

    return core_content


def test_main_with_content():
    content = "What is the capital of France?"
    result = runner.invoke(main, ['prompt', content])
    assert result.exit_code == 0
    assert _check_output_format(result.output)
    assert "Paris" in result.output


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

    with open(temp_config_path, "w", encoding='utf-8') as temp_config_file:
        json.dump(config_data, temp_config_file)

    original_cwd = os.getcwd()
    os.chdir(temp_dir)

    content = "What is the capital of Spain?"
    result = runner.invoke(main, ['prompt', content])
    assert result.exit_code == 0
    assert _check_output_format(result.output)
    assert "Madrid" in result.output

    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)


@pytest.fixture(name="temp_files")
def fixture_temp_files(tmpdir):
    instruct0 = tmpdir.join('instruct0.txt')
    instruct0.write("Summarize the following user message.\n")
    instruct1 = tmpdir.join('instruct1.txt')
    instruct1.write("The summary must be lowercased under 10 characters without any punctuation.\n")
    instruct2 = tmpdir.join('instruct2.txt')
    instruct2.write("The summary must be lowercased under 15 characters without any punctuation."
                    "Leverage the context to generate the summary.\n")
    context = tmpdir.join("context.txt")
    context.write("<context> This year is 2023.")
    return str(instruct0), str(instruct1), str(instruct2), str(context)


def test_main_with_instruct(temp_files):
    files = f'{temp_files[0]},{temp_files[1]}'
    result = runner.invoke(main, ['prompt', '--instruct', files,
                                  "This summer is really scorching."])
    assert result.exit_code == 0
    assert _get_core_content(result.output) == "hot summer\n"


def test_main_with_instruct_and_context(temp_files):
    instruct_files = f"{temp_files[0]},{temp_files[2]}"
    result = runner.invoke(main, ['prompt', '--instruct', instruct_files,
                                  '--context', temp_files[3],
                                  "This summer is really scorching."])
    assert result.exit_code == 0
    assert _get_core_content(result.output) == "hot summer 2023\n"
