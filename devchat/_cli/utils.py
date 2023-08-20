from contextlib import contextmanager
import json
import os
import sys
from typing import Tuple
import rich_click as click
from devchat.utils import find_root_dir, git_ignore, setup_logger, get_logger

logger = get_logger(__name__)


@contextmanager
def handle_errors():
    """Handle errors in the CLI."""
    try:
        yield
    except Exception as error:
        logger.exception(error)
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)


def init_dir() -> Tuple[dict, str]:
    root_dir = find_root_dir()
    if not root_dir:
        click.echo("Error: Failed to find home to store .chat", err=True)
        sys.exit(1)
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
