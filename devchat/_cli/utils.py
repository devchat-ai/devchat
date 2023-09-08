from contextlib import contextmanager
import os
import sys
from typing import Tuple, List, Optional
from git import Repo, InvalidGitRepositoryError, GitCommandError
import rich_click as click
from devchat.config import ConfigManager, ModelConfig
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
        click.echo(f"{type(error).__name__}: {error}", err=True)
        sys.exit(1)


def init_dir() -> Tuple[str, str]:
    """
    Initialize the chat directories.

    Returns:
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

    try:
        setup_logger(os.path.join(repo_chat_dir, 'error.log'))
        add_gitignore(repo_chat_dir, '*')
    except Exception as exc:
        logger.error("Failed to setup logger or add .gitignore: %s", exc)

    return repo_chat_dir, user_chat_dir


def valid_git_repo(target_dir: str, valid_urls: List[str]) -> bool:
    """
    Check if a directory is a valid Git repository and if its URL is in a list of valid URLs.

    :param target_dir: The path of the directory to check.
    :param valid_urls: A list of valid Git repository URLs.
    :return: True if the directory is a valid Git repository with a valid URL, False otherwise.
    """
    try:
        repo = Repo(target_dir)
        repo_url = next(repo.remote().urls)
        return repo_url in valid_urls
    except InvalidGitRepositoryError:
        logger.exception("Not a valid Git repository: %s", target_dir)
        return False


def clone_git_repo(target_dir: str, repo_urls: List[str]):
    """
    Clone a Git repository from a list of possible URLs.

    :param target_dir: The path where the repository should be cloned.
    :param repo_urls: A list of possible Git repository URLs.
    """
    for url in repo_urls:
        try:
            click.echo(f"Cloning repository {url} to {target_dir}")
            Repo.clone_from(url, target_dir)
            click.echo("Cloned successfully")
            return
        except GitCommandError:
            logger.exception("Failed to clone repository %s to %s", url, target_dir)
            continue
    raise GitCommandError(f"Failed to clone repository to {target_dir}")


def model_config(repo_chat_dir: str, user_chat_dir: str,
                 model: Optional[str] = None) -> ModelConfig:
    legacy_path = os.path.join(repo_chat_dir, 'config.json')
    if os.path.exists(legacy_path):
        os.rename(legacy_path, legacy_path + '.old')

    config = ConfigManager(user_chat_dir)
    return config.get_model_config(model)
