"""
This module contains the main function for the DevChat CLI.
"""


from typing import Optional
import json
import click
from pydantic import ValidationError
from devchat.message import Message
from devchat.chat.openai_chat import OpenAIChatConfig, OpenAIChat
from devchat.prompt import Prompt


@click.group()
def main():
    pass


@main.command()
@click.argument('content', required=False)
@click.option('-h', '--help', is_flag=True, help='Show the help message and exit.')
def prompt(content: Optional[str], help: bool):
    """
    Main function to run the chat application.

    This function initializes the chat system based on the specified large language model (LLM),
    and performs interactions with the user by sending prompts and retrieving responses.
    """
    if help:
        print_help()
        return

    if content is None:
        content = click.get_text_stream('stdin').read()

    if content == '':
        return

    default_config_data = {
        'llm': 'OpenAI',
        'OpenAI': {
            'model': 'gpt-3.5-turbo',
            'temperature': 0.2
        }
    }

    try:
        with open('.chatconfig.json', 'r', encoding='utf-8') as file:
            config_data = json.load(file)
    except FileNotFoundError:
        config_data = default_config_data

    message = Message("user", content)

    llm = config_data.get('llm')

    if llm == 'OpenAI':
        try:
            openai_config = OpenAIChatConfig(**config_data['OpenAI'])
            chat = OpenAIChat(openai_config)
            prompt = Prompt(chat.config.model)
            chat.prompt([message])

            if openai_config.stream:
                response_iterator = chat.stream_response()
                for response_chunk in response_iterator:
                    delta_str = prompt.append_response(str(response_chunk))
                    if delta_str is None:
                        click.echo()
                    else:
                        click.echo(delta_str, nl=False)
                for i in range(1, len(prompt.responses)):
                    click.echo(f"[{i}]: {prompt.responses[i].content}")

            else:
                response_str = str(chat.complete_response())
                prompt.set_response(response_str)
                if len(prompt.responses) == 1:
                    click.echo(prompt.responses[0].content)
                else:
                    for index, response in prompt.responses.items():
                        click.echo(f"[{index}]: {response.content}")

        except ValidationError as error:
            click.echo(f"Error: {error}")
    else:
        click.echo(f"Unknown LLM: {llm}")


@main.command()
@click.option('--skip', default=0, help='Skip number prompts before showing the prompt history.')
@click.option('--max-count', default=100, help='Limit the number of commits to output.')
def log(skip, max_count):
    """
    Show the prompt history.
    """
    # Implement the logic to display the prompt history based on the `skip` and `max_count` options.
    pass


def print_help():
    """
    Print the help message for the DevChat CLI.
    """
    help_text = """
    This manual provides instructions on how to use the DevChat CLI,
    a command-line interface for interacting with a large language model (LLM).

    Usage
    -----

    To use the DevChat CLI, run the following command:

    ```
    devchat [OPTIONS] [CONTENT]
    ```

    Arguments
    ---------

    - `content` (optional): One or more lines of text as a message or prompt.
                            If not provided, the CLI will read from standard input.

    Options
    -------

    - `-h`, `--help`: Show the help manual and exit.

    Examples
    --------

    ### Single-line input

    To send a single-line message to the LLM, provide the content as an argument:

    ```
    devchat "What is the capital of France?"
    ```

    ### Multi-line input using here-doc

    To send a multi-line message to the LLM, use the here-doc syntax:

    ```bash
    devchat << 'EOF'
    What is the capital of France?
    Can you tell me more about its history?
    EOF
    ```
    Note the quotes around EOF in the first line, to prevent the shell from expanding variables.

    Configuration
    -------------

    The DevChat CLI reads its configuration from a file `.chatconfig.json` in the current directory.
    If the file is not found, it uses the following default configuration:

    ```json
    {
        "llm": "OpenAI",
        "OpenAI": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.2
        }
    }
    ```

    To customize the configuration, create a `.chatconfig.json` file in the current directory and
    modify the settings as needed. We recoommend the following settings:
    {
        "llm": "OpenAI",
        "OpenAI": {
            "model": "gpt-4",
            "temperature": 0.2,
            "stream": true
        }
    }

    Note: To use OpenAI's APIs, you must have an API key to run the CLI.
    Run the following command line with your API key:

    ```bash
    export OPENAI_API_KEY="sk-..."
    ```
    """
    click.echo(help_text)
