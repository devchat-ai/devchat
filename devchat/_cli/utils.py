from contextlib import contextmanager
import os
import sys
import shutil
from typing import Tuple, List, Optional, Any
import zipfile

from devchat._cli.errors import MissContentInPromptException
from devchat.utils import find_root_dir, add_gitignore, setup_logger, get_logger

logger = get_logger(__name__)


def download_and_extract_workflow(workflow_url, target_dir):
    import requests
    # Download the workflow zip file
    response = requests.get(workflow_url, stream=True, timeout=10)
    # Downaload file to temp dir
    os.makedirs(target_dir, exist_ok=True)
    zip_path = os.path.join(target_dir, 'workflow.zip')
    with open(zip_path, 'wb') as file_handle:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file_handle.write(chunk)

    # Extract the zip file
    parent_dir = os.path.dirname(target_dir)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(parent_dir)

    # Delete target directory if exists
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    # Rename extracted directory to target directory
    extracted_dir = os.path.join(parent_dir, 'workflows-main')
    os.rename(extracted_dir, target_dir)


@contextmanager
def handle_errors():
    # import openai
    """Handle errors in the CLI."""
    try:
        yield
    # except openai.APIError as error:
    #     logger.exception(error)
    #     print(f"{type(error).__name__}: {error.type}", file=sys.stderr)
    #     sys.exit(1)
    except MissContentInPromptException:
        print("Miss content in prompt command.", file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        # import traceback
        # traceback.print_exc()
        logger.exception(error)
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)


repo_chat_dir = None
user_chat_dir = None
def init_dir() -> Tuple[str, str]:
    """
    Initialize the chat directories.

    Returns:
        repo_chat_dir: The chat directory in the repository.
        user_chat_dir: The chat directory in the user's home.
    """
    global repo_chat_dir
    global user_chat_dir
    if repo_chat_dir and user_chat_dir:
        return repo_chat_dir, user_chat_dir

    repo_dir, user_dir = find_root_dir()
    if not repo_dir and not user_dir:
        print(f"Error: Failed to find home for .chat: {repo_dir}, {user_dir}", file=sys.stderr)
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
        print(f"Error: Failed to create {repo_chat_dir} and {user_chat_dir}", file=sys.stderr)
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
        from git import Repo, InvalidGitRepositoryError
    except Exception:
        pass

    try:
        repo = Repo(target_dir)
        repo_url = next(repo.remote().urls)
        return repo_url in valid_urls
    except InvalidGitRepositoryError:
        logger.exception("Not a valid Git repository: %s", target_dir)
        return False
    except Exception:
        return False


def clone_git_repo(target_dir: str, repo_urls: List[Tuple[str, str]]):
    """
    Clone a Git repository from a list of possible URLs.

    :param target_dir: The path where the repository should be cloned.
    :param repo_urls: A list of possible Git repository URLs.
    """
    try:
        from git import Repo, GitCommandError
    except Exception:
        pass

    for url, branch in repo_urls:
        try:
            print(f"Cloning repository {url} to {target_dir}")
            Repo.clone_from(url, target_dir, branch=branch)
            print("Cloned successfully")
            return
        except GitCommandError:
            logger.exception("Failed to clone repository %s to %s", url, target_dir)
            continue
    raise GitCommandError(f"Failed to clone repository to {target_dir}")


def get_model_config(user_chat_dir: str,
                     model: Optional[str] = None) -> Tuple[str, Any]:
    from devchat.config import ConfigManager
    manager = ConfigManager(user_chat_dir)
    return manager.model_config(model)
