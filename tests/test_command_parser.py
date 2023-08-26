import tempfile
import pytest
from devchat.engine import parse_command, Command


def test_parse_command():
    # Test with a valid configuration file
    with tempfile.NamedTemporaryFile('w', delete=False) as config_file:
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
        assert command.description == 'Get the current weather in a given location'
        assert 'location' in command.parameters
        assert command.parameters['unit'].default == 'celsius'
        assert command.steps[0]['run'] == './get_weather --location=$location --unit=$unit'

    with tempfile.NamedTemporaryFile('w', delete=False) as config_file:
        config_file.write("""
        description: Prompt for /code
        parameters:
        """)
        config_file.seek(0)
        command = parse_command(config_file.name)
        assert command.parameters is None
        assert command.steps is None

        # Test with an invalid configuration file
        with tempfile.NamedTemporaryFile('w', delete=False) as config_file:
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
        parse_command('path/to/non_existent_file.yaml')
