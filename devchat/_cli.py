"""
This module contains the main function for the DevChat CLI.
"""
from contextlib import contextmanager
import json
import os
import sys
from typing import List, Optional, Tuple
import importlib.metadata
import rich_click as click
from devchat.store import Store
from devchat.openai import OpenAIChatConfig, OpenAIChat
from devchat.assistant import Assistant
from devchat.utils import find_root_dir, git_ignore, parse_files
from devchat.utils import setup_logger, get_logger

logger = get_logger(__name__)
click.rich_click.USE_MARKDOWN = True


@click.group()
@click.version_option(importlib.metadata.version("devchat"), '--version',
                      message='DevChat %(version)s')
def main():
    """DevChat CLI: A command-line interface for DevChat."""


@contextmanager
def handle_errors():
    """Handle errors in the CLI."""
    try:
        yield
    except Exception as error:
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
@click.option('--config', 'config_str',
              help='Specify a JSON string to overwrite the configuration for this prompt.')
@click.option('-f', '--functions', type=click.Path(exists=True),
              help='Path to a JSON file with functions for the prompt.')
@click.option('-n', '--function-name',
              help='Specify the function name when the content is the output of a function.')
def prompt(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None,
           functions: Optional[str] = None, function_name: Optional[str] = None):
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

            if config_str is not None:
                config_json = json.loads(config_str)
                config['OpenAI'].update(config_json)

            openai_config = OpenAIChatConfig(model=model,
                                             **config['OpenAI'])

            chat = OpenAIChat(openai_config)
            store = Store(chat_dir, chat)

            assistant = Assistant(chat, store)
            if 'tokens-per-prompt' in config:
                assistant.token_limit = config['tokens-per-prompt']

            functions_data = None
            if functions is not None:
                with open(functions, 'r', encoding="utf-8") as f_file:
                    functions_data = json.load(f_file)
            assistant.make_prompt(content, instruct_contents, context_contents, functions_data,
                                  parent=parent, references=reference,
                                  function_name=function_name)

            for response in assistant.iterate_response():
                click.echo(response, nl=False)
        else:
            click.echo(f"Error: Invalid LLM in configuration '{provider}'", err=True)
            sys.exit(os.EX_DATAERR)


@main.command()
@click.option('--skip', default=0, help='Skip number prompts before showing the prompt history.')
@click.option('-n', '--max-count', default=1, help='Limit the number of commits to output.')
@click.option('-t', '--topic', 'topic_root', default=None,
              help='Hash of the root prompt of the topic to select prompts from.')
@click.option('--delete', default=None, help='Delete a leaf prompt from the log.')
def log(skip, max_count, topic_root, delete):
    """
    Manage the prompt history.
    """
    if delete and (skip != 0 or max_count != 1 or topic_root is not None):
        click.echo("Error: The --delete option cannot be used with other options.", err=True)
        sys.exit(os.EX_USAGE)

    config, chat_dir = init_dir()

    with handle_errors():
        provider = config.get('provider')
        if provider == 'OpenAI':
            openai_config = OpenAIChatConfig(model=config['model'], **config['OpenAI'])
            chat = OpenAIChat(openai_config)
            store = Store(chat_dir, chat)
        else:
            click.echo(f"Error: Invalid LLM in configuration '{provider}'", err=True)
            sys.exit(os.EX_DATAERR)

        if delete:
            success = store.delete_prompt(delete)
            if success:
                click.echo(f"Prompt {delete} deleted successfully.")
            else:
                click.echo(f"Failed to delete prompt {delete}.")
        else:
            recent_prompts = store.select_prompts(skip, skip + max_count, topic_root)
            logs = []
            for record in recent_prompts:
                try:
                    logs.append(record.shortlog())
                except Exception as exc:
                    logger.exception(exc)
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

    with handle_errors():
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
            for topic_data in topics:
                try:
                    topic_data.update({'root_prompt': topic_data['root_prompt'].shortlog()})
                except Exception as exc:
                    logger.exception(exc)
                    continue
            click.echo(json.dumps(topics, indent=2))
