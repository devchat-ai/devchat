from contextlib import contextmanager
import json
import os
import sys
from typing import Tuple
import rich_click as click
from devchat.utils import find_root_dir, add_gitignore, setup_logger, get_logger

logger = get_logger(__name__)


@contextmanager
def handle_errors():
    """Handle errors in the CLI."""
    try:
        yield
    except Exception as error:
        # import traceback
        # traceback.print_exc()
        logger.exception(error)
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)


def init_dir() -> Tuple[dict, str, str]:
    """
    Initialize the chat directory.

    Returns:
        config_data: The configuration data.
        repo_chat_dir: The chat directory in the repository.
        user_chat_dir: The chat directory in the user's home.
    """
    repo_dir, user_dir = find_root_dir()
    if not repo_dir and not user_dir:
        click.echo(f"Error: Failed to find home for .chat: {repo_dir}, {user_dir}", err=True)
        sys.exit(1)

    if not repo_dir:
        repo_dir = user_dir
    elif not user_dir:
        user_dir = repo_dir

    try:
        repo_chat_dir = os.path.join(repo_dir, ".chat")
        if not os.path.exists(repo_chat_dir):
            os.makedirs(repo_chat_dir)
    except Exception:
        pass

    try:
        user_chat_dir = os.path.join(user_dir, ".chat")
        if not os.path.exists(user_chat_dir):
            os.makedirs(user_chat_dir)
    except Exception:
        pass

    if not os.path.isdir(repo_chat_dir):
        repo_chat_dir = user_chat_dir
    if not os.path.isdir(user_chat_dir):
        user_chat_dir = repo_chat_dir
    if not os.path.isdir(repo_chat_dir) or not os.path.isdir(user_chat_dir):
        click.echo(f"Error: Failed to create {repo_chat_dir} and {user_chat_dir}", err=True)
        sys.exit(1)

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
        with open(os.path.join(user_chat_dir, 'config.json'), 'r', encoding='utf-8') as file:
            config_data = json.load(file)
    except Exception:
        config_data = default_config_data

    try:
        setup_logger(os.path.join(repo_chat_dir, 'error.log'))
        add_gitignore(repo_chat_dir, '*')
    except Exception as exc:
        logger.error("Failed to setup logger or add .gitignore: %s", exc)

    return config_data, repo_chat_dir, user_chat_dir
