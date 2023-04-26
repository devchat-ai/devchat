"""
This module contains the main function for the DevChat CLI.
"""


import os
import time
from typing import Optional
import json
import sys
import rich_click as click
from contextlib import contextmanager
from devchat.message import Message
from devchat.chat.openai_chat import OpenAIChatConfig, OpenAIChat
from devchat.prompt import Prompt
from devchat.utils import get_git_user_info, parse_file_paths


click.rich_click.USE_MARKDOWN = True


@click.group()
def main():
    pass


@contextmanager
def handle_errors():
    try:
        yield
    except Exception as error:
        click.echo(f"Error: {error}", err=True)
        sys.exit(os.EX_SOFTWARE)


@main.command()
@click.argument('content', required=False)
@click.option('-p', '--parent', help='Input the previous prompt hash to continue the conversation.')
@click.option('-r', '--reference', help='Input one or more specific previous prompt hashes to '
              'include in the current prompt.')
@click.option('--header', help='Input one or more files for the prompt header.')
@click.option('--context', help='Input one or more files for the prompt context.')
def prompt(content: Optional[str], parent: Optional[str], reference: Optional[str],
           header: Optional[str], context: Optional[str]):
    """
    Main function to run the chat application.

    This function initializes the chat system based on the specified large language model (LLM),
    and performs interactions with the user by sending prompts and retrieving responses.

    Examples
    --------

    To send a single-line message to the LLM, provide the content as an argument:

    ```bash
    devchat prompt "What is the capital of France?"
    ```

    To send a multi-line message to the LLM, use the here-doc syntax:

    ```bash
    devchat prompt << 'EOF'
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
    ```json
    {
        "llm": "OpenAI",
        "OpenAI": {
            "model": "gpt-4",
            "temperature": 0.2,
            "stream": true
        }
    }
    ```

    Note: To use OpenAI's APIs, you must have an API key to run the CLI.
    Run the following command line with your API key:

    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

    """
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

    with handle_errors():
        if content is None:
            content = click.get_text_stream('stdin').read()

        if content == '':
            return

        parse_file_paths(header)
        parse_file_paths(context)

        message = Message("user", content)

        llm = config_data.get('llm')

        if llm == 'OpenAI':
            openai_config = OpenAIChatConfig(**config_data['OpenAI'])
            chat = OpenAIChat(openai_config)

            user, email = get_git_user_info()
            prompt = Prompt(chat.config.model, user, email)
            chat.prompt([message])

            if openai_config.stream:
                response_iterator = chat.stream_response()
                for response_chunk in response_iterator:
                    delta_str = prompt.append_response(str(response_chunk))
                    if delta_str is None:
                        click.echo(f'\n\nprompt {prompt.hash(0)}\n')
                    else:
                        click.echo(delta_str, nl=False)
                for index in range(1, len(prompt.responses)):
                    click.echo(prompt.formatted_response(index) + '\n')

            else:
                response_str = str(chat.complete_response())
                prompt.set_response(response_str)
                for index in prompt.responses.keys():
                    click.echo(prompt.formatted_response(index) + '\n')
        else:
            click.echo(f"Error: Invalid LLM in configuration '{llm}'. Expected 'OpenAI'.", err=True)
            sys.exit(os.EX_DATAERR)


@main.command()
@click.option('--skip', default=0, help='Skip number prompts before showing the prompt history.')
@click.option('--max-count', default=100, help='Limit the number of commits to output.')
def log(skip, max_count):
    """
    Show the prompt history.
    """
    # Implement the logic to display the prompt history based on the `skip` and `max_count` options.
    logs = []
    for n in range(skip, skip + max_count):
        m = Message("user", f"Prompt {n}")
        name, email = get_git_user_info()
        p = Prompt("gpt-3.5-turbo", name, email)
        p.append_message(m)
        r = {
            "model": "gpt-3.5-turbo-0301",
            "created": int(time.time()),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Response {n}",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        }
        p.set_response(json.dumps(r))
        logs = p.shortlog() + logs
    click.echo(logs)
