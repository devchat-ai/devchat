import os
import tempfile

import pytest

from devchat.engine import Command, CommandParser, Namespace, parse_command


def test_parse_command():
    # Test with a valid configuration file with most fields filled
    with tempfile.NamedTemporaryFile("w", delete=False) as config_file:
        config_file.write("""
        description: Get the current weather in a given location
        parameters:
            location:
                type: string
                description: The city and state, e.g. San Francisco, CA
            unit:
                type: string
                enum: [celsius, fahrenheit]
                default: celsius
        steps:
            - run:
                ./get_weather --location=$location --unit=$unit
        """)
        config_file.seek(0)
        command = parse_command(config_file.name)
        assert isinstance(command, Command)
        command = command.dict()
        assert command["description"] == "Get the current weather in a given location"
        assert "location" in command["parameters"]
        assert command["parameters"]["unit"]["default"] == "celsius"
        assert command["steps"][0]["run"] == "./get_weather --location=$location --unit=$unit"

    # Test with a valid configuration file with missing optional fields
    with tempfile.NamedTemporaryFile("w", delete=False) as config_file:
        config_file.write("""
        description: Prompt for /code
        parameters:
        """)
        config_file.seek(0)
        command = parse_command(config_file.name)
        assert command.parameters is None
        assert command.steps is None

    # Test with an invalid configuration file
    with tempfile.NamedTemporaryFile("w", delete=False) as config_file:
        config_file.write("""
        description:
        parameters:
            location:
                type: string
        """)
        config_file.seek(0)
        with pytest.raises(Exception):
            parse_command(config_file.name)

    # Test with a non-existent file
    with pytest.raises(FileNotFoundError):
        parse_command("path/to/non_existent_file.yml")


def test_command_parser(tmp_path):
    # Create a Namespace instance with the temporary directory as the root path
    namespace = Namespace(tmp_path)
    command_parser = CommandParser(namespace)

    # Test with a valid configuration file with most fields filled
    os.makedirs(os.path.join(tmp_path, "usr", "a", "b", "c"), exist_ok=True)
    command_file_path = os.path.join(tmp_path, "usr", "a", "b", "c", "command.yml")
    with open(command_file_path, "w", encoding="utf-8") as file:
        file.write("""
        description: Get the current weather in a given location
        parameters:
            location:
                type: string
                description: The city and state, e.g. San Francisco, CA
            unit:
                type: string
                enum: [celsius, fahrenheit]
                default: celsius
        steps:
            - run:
                ./get_weather --location=$location --unit=$unit
        """)
    command = command_parser.parse("a.b.c")
    command = command.dict()
    assert command["description"] == "Get the current weather in a given location"
    assert "location" in command["parameters"]
    assert command["parameters"]["unit"]["default"] == "celsius"
    assert command["steps"][0]["run"] == "./get_weather --location=$location --unit=$unit"

    # Test with a valid configuration file with missing optional fields
    os.makedirs(os.path.join(tmp_path, "usr", "d", "e", "f"), exist_ok=True)
    command_file_path = os.path.join(tmp_path, "usr", "d", "e", "f", "command.yml")
    with open(command_file_path, "w", encoding="utf-8") as file:
        file.write("""
        description: Prompt for /code
        parameters:
        """)
    command = command_parser.parse("d.e.f")
    command = command.dict()
    assert command["description"] == "Prompt for /code"
    assert command["parameters"] is None
    assert command["steps"] is None

    # Test with an invalid configuration file
    os.makedirs(os.path.join(tmp_path, "usr", "g", "h", "i"), exist_ok=True)
    command_file_path = os.path.join(tmp_path, "usr", "g", "h", "i", "command.yml")
    with open(command_file_path, "w", encoding="utf-8") as file:
        file.write("""
        description:
        parameters:
            location:
                type: string
        """)
    with pytest.raises(Exception):
        command_parser.parse("g.h.i")

    # Test with a non-existent command
    command = command_parser.parse("j.k.l")
    assert command is None
