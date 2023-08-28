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

    try:
        repo_chat_dir = os.path.join(repo_dir, ".chat")
        if not os.path.exists(repo_chat_dir):
            os.makedirs(repo_chat_dir)
    except Exception:
        click.echo(f"Error: Failed to create {repo_chat_dir}", err=True)

    try:
        user_chat_dir = os.path.join(user_dir, ".chat")
        if not os.path.exists(user_chat_dir):
            os.makedirs(user_chat_dir)
    except Exception:
        click.echo(f"Error: Failed to create {user_chat_dir}", err=True)

    if not os.path.isdir(repo_chat_dir):
        repo_chat_dir = user_chat_dir
    if not os.path.isdir(user_chat_dir):
        user_chat_dir = repo_chat_dir
    if not os.path.isdir(repo_chat_dir):
        click.echo(f"Error: Failed to create {repo_chat_dir}", err=True)
        sys.exit(1)
    if not os.path.isdir(user_chat_dir):
        click.echo(f"Error: Failed to create {user_chat_dir}", err=True)
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
        workflows_dir = os.path.join(user_chat_dir, 'workflows')
        if not os.path.exists(workflows_dir):
            os.makedirs(workflows_dir)
    except Exception:
        click.echo(f"Error: Failed to create {workflows_dir}", err=True)
    if not os.path.isdir(workflows_dir):
        sys.exit(1)

    try:
        setup_logger(os.path.join(repo_chat_dir, 'error.log'))
        git_ignore(repo_chat_dir, '*')
    except Exception as exc:
        click.echo(f"Error: Failed to setup logger or .gitignore: {exc}", err=True)

    return config_data, repo_chat_dir, user_chat_dir
