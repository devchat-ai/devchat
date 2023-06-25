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
from devchat.utils import find_root_dir, git_ignore, parse_files
from devchat.utils import setup_logger, get_logger


click.rich_click.USE_MARKDOWN = True


@click.group()
def main():
    """DevChat CLI: A command-line interface for DevChat."""


@contextmanager
def handle_errors():
    """Handle errors in the CLI."""
    try:
        yield
    except Exception as error:
        logger = get_logger(__name__)
        logger.exception(error)
        click.echo(f"Error: {error}", err=True)
        sys.exit(os.EX_SOFTWARE)


def init_dir() -> Tuple[dict, str]:
    root_dir = find_root_dir()
    if not root_dir:
        click.echo("Error: Failed to find home to store .chat", err=True)
        sys.exit(os.EX_DATAERR)
    chat_dir = os.path.join(root_dir, ".chat")
    if not os.path.exists(chat_dir):
        os.makedirs(chat_dir)

    default_config_data = {
        "model": "gpt-4",
        "tokens-per-prompt": 6000,
        "provider": "OpenAI",
        "OpenAI": {
            "temperature": 0,
            "stream": True
        }
    }

    try:
        with open(os.path.join(chat_dir, 'config.json'), 'r', encoding='utf-8') as file:
            config_data = json.load(file)
    except Exception:
        config_data = default_config_data

    setup_logger(os.path.join(chat_dir, 'error.log'))
    git_ignore(chat_dir, '*')
    return config_data, chat_dir


@main.command()
@click.argument('content', required=False)
@click.option('-p', '--parent', help='Input the parent prompt hash to continue the conversation.')
@click.option('-r', '--reference', multiple=True,
              help='Input one or more specific previous prompts to include in the current prompt.')
@click.option('-i', '--instruct', multiple=True,
              help='Add one or more files to the prompt as instructions.')
@click.option('-c', '--context', multiple=True,
              help='Add one or more files to the prompt as a context.')
@click.option('-m', '--model', help='Specify the model to temporarily use for the prompt '
              '(prefer to modify .chat/config.json).')
def prompt(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]], model: Optional[str]):
    """
    Main function to run the chat application.

    This function initializes the chat system based on the specified large language model (LLM),
    and performs interactions with the LLM by sending prompts and retrieving responses.

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

    DevChat CLI reads its configuration from `.chat/config.json`
    in your current Git or SVN root directory.
    If the file is not found, it uses the following default configuration:
    ```json
    {
        "model": "gpt-4",
        "tokens-per-prompt": 6000,
        "provider": "OpenAI",
        "OpenAI": {
            "temperature": 0,
            "stream": true
        }
    }
    ```

    To customize the configuration, create `.chat/config.json`
    in your current Git or SVN root directory
    and modify the settings as needed.

    Note: To use OpenAI's APIs, you must have an API key to run the CLI.
    Run the following command line with your API key:

    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

    """
    config, chat_dir = init_dir()

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
            store = Store(chat_dir, chat)

            assistant = Assistant(chat, store)
            if 'tokens-per-prompt' in config:
                assistant.token_limit = config['tokens-per-prompt']

            assistant.make_prompt(content, instruct_contents, context_contents,
                                  parent, reference)

            for response in assistant.iterate_response():
                click.echo(response, nl=False)
        else:
            click.echo(f"Error: Invalid LLM in configuration '{provider}'", err=True)
            sys.exit(os.EX_DATAERR)


@main.command()
@click.option('--skip', default=0, help='Skip number prompts before showing the prompt history.')
@click.option('-n', '--max-count', default=100, help='Limit the number of commits to output.')
@click.option('-t', '--topic', 'topic_root', default=None,
              help='Hash of the root prompt of the topic to select prompts from.')
def log(skip, max_count, topic_root):
    """
    Show the prompt history.
    """
    config, chat_dir = init_dir()
    provider = config.get('provider')
    if provider == 'OpenAI':
        openai_config = OpenAIChatConfig(model=config['model'], **config['OpenAI'])
        chat = OpenAIChat(openai_config)
        store = Store(chat_dir, chat)
    else:
        click.echo(f"Error: Invalid LLM in configuration '{provider}'", err=True)
        sys.exit(os.EX_DATAERR)

    recent_prompts = store.select_prompts(skip, skip + max_count, topic_root)
    logs = []
    for record in recent_prompts:
        try:
            logs.append(record.shortlog())
        except Exception:
            continue
    click.echo(json.dumps(logs, indent=2))


@main.command()
@click.option('--list', '-l', 'list_topics', is_flag=True,
              help='List topics in reverse chronological order.')
@click.option('--skip', default=0, help='Skip number of topics before showing the list.')
@click.option('-n', '--max-count', default=100, help='Limit the number of topics to output.')
def topic(list_topics: bool, skip: int, max_count: int):
    """
    Manage topics.
    """
    config, chat_dir = init_dir()
    provider = config.get('provider')
    if provider == 'OpenAI':
        openai_config = OpenAIChatConfig(model=config['model'], **config['OpenAI'])
        chat = OpenAIChat(openai_config)
        store = Store(chat_dir, chat)
    else:
        click.echo(f"Error: Invalid LLM in configuration '{provider}'", err=True)
        sys.exit(os.EX_DATAERR)

    if list_topics:
        topics = store.select_topics(skip, skip + max_count)
        topic_logs = []
        for topic_data in topics:
            try:
                topic_logs.append(topic_data['root_prompt'].shortlog())
            except Exception:
                continue
        click.echo(json.dumps(topic_logs, indent=2))
