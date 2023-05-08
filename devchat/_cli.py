"""
This module contains the main function for the DevChat CLI.
"""
from contextlib import contextmanager
import json
import os
import sys
from typing import List, Optional, Tuple
import rich_click as click
from devchat.store import Store
from devchat.openai import OpenAIChatConfig, OpenAIChat
from devchat.assistant import Assistant
from devchat.utils import find_git_root, git_ignore, parse_files


click.rich_click.USE_MARKDOWN = True


@click.group()
def main():
    """DevChat CLI: A command-line interface for the DevChat chatbot."""


@contextmanager
def handle_errors():
    """Handle errors in the CLI."""
    try:
        yield
    except Exception as error:
        click.echo(f"Error: {error}", err=True)
        sys.exit(os.EX_SOFTWARE)


def init_dir() -> Tuple[dict, Store]:
    git_root = find_git_root()
    chat_dir = os.path.join(git_root, ".chat")
    if not os.path.exists(chat_dir):
        os.makedirs(chat_dir)

    default_config_data = {
        'model': 'gpt-3.5-turbo',
        'provider': 'OpenAI',
        'OpenAI': {
            'temperature': 0.2
        }
    }

    try:
        with open(os.path.join(chat_dir, 'config.json'), 'r', encoding='utf-8') as file:
            config_data = json.load(file)
    except FileNotFoundError:
        config_data = default_config_data

    store = Store(chat_dir)
    git_ignore(git_root, store.graph_path, store.db_path)
    return config_data, store


@main.command()
@click.argument('content', required=False)
@click.option('-p', '--parent', help='Input the parent prompt hash to continue the conversation.')
@click.option('-r', '--reference', multiple=True,
              help='Input one or more specific previous prompts to include in the current prompt.')
@click.option('-i', '--instruct', multiple=True,
              help='Add one or more files to the prompt as instructions.')
@click.option('-c', '--context', multiple=True,
              help='Add one or more files to the prompt as a context.')
@click.option('-m', '--model', help='Specify the model to use for the prompt.')
def prompt(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]], model: Optional[str]):
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
        "model": "gpt-3.5-turbo",
        "provider": "OpenAI",
        "OpenAI": {
            "temperature": 0.2
        }
    }
    ```

    To customize the configuration, create a `.chatconfig.json` file in the current directory and
    modify the settings as needed. We recoommend the following settings:
    ```json
    {
        "model": "gpt-4",
        "provider": "OpenAI",
        "OpenAI": {
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
    config, store = init_dir()

    with handle_errors():
        if content is None:
            content = click.get_text_stream('stdin').read()

        if content == '':
            return

        instruct_contents = parse_files(instruct)
        context_contents = parse_files(context)

        provider = config.get('provider')
        if provider == 'OpenAI':
            if model is None:
                model = config['model']
            openai_config = OpenAIChatConfig(model=model, **config['OpenAI'])

            chat = OpenAIChat(openai_config)

            openai_asisstant = Assistant(chat, store)
            openai_asisstant.make_prompt(content, instruct_contents, context_contents,
                                         parent, reference)

            for response in openai_asisstant.iterate_response():
                click.echo(response, nl=False)
        else:
            click.echo(f"Error: Invalid LLM in configuration '{provider}'", err=True)
            sys.exit(os.EX_DATAERR)


@main.command()
@click.option('--skip', default=0, help='Skip number prompts before showing the prompt history.')
@click.option('--max-count', default=100, help='Limit the number of commits to output.')
def log(skip, max_count):
    """
    Show the prompt history.
    """
    _, store = init_dir()

    recent_prompts = store.select_recent(skip, skip + max_count)

    logs = []
    for record in recent_prompts:
        logs.append(record.shortlog())
    click.echo(json.dumps(logs, indent=2))
