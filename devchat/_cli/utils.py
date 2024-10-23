import os
import sys
import zipfile
from contextlib import contextmanager
from typing import Any, List, Optional, Tuple

from devchat._cli.errors import MissContentInPromptException
from devchat.utils import add_gitignore, find_root_dir, get_logger, rmtree, setup_logger

logger = get_logger(__name__)


def download_and_extract_workflow(workflow_url, target_dir):
    import requests

    # Download the workflow zip file
    response = requests.get(workflow_url, stream=True, timeout=10)
    # Downaload file to temp dir
    os.makedirs(target_dir, exist_ok=True)
    zip_path = os.path.join(target_dir, "workflow.zip")
    with open(zip_path, "wb") as file_handle:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file_handle.write(chunk)

    # Extract the zip file
    parent_dir = os.path.dirname(target_dir)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(parent_dir)

    # Delete target directory if exists
    if os.path.exists(target_dir):
        rmtree(target_dir)

    # Rename extracted directory to target directory
    extracted_dir = os.path.join(parent_dir, "workflows-main")
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


REPO_CHAT_DIR = None
USER_CHAT_DIR = None


def init_dir() -> Tuple[str, str]:
    """
    Initialize the chat directories.

    Returns:
        REPO_CHAT_DIR: The chat directory in the repository.
        USER_CHAT_DIR: The chat directory in the user's home.
    """
    global REPO_CHAT_DIR
    global USER_CHAT_DIR
    if REPO_CHAT_DIR and USER_CHAT_DIR:
        return REPO_CHAT_DIR, USER_CHAT_DIR

    repo_dir, user_dir = find_root_dir()
    if not repo_dir and not user_dir:
        print(f"Error: Failed to find home for .chat: {repo_dir}, {user_dir}", file=sys.stderr)
        sys.exit(1)

    if not repo_dir:
        repo_dir = user_dir
    elif not user_dir:
        user_dir = repo_dir

    try:
        REPO_CHAT_DIR = os.path.join(repo_dir, ".chat")
        if not os.path.exists(REPO_CHAT_DIR):
            os.makedirs(REPO_CHAT_DIR)
    except Exception:
        pass

    try:
        USER_CHAT_DIR = os.path.join(user_dir, ".chat")
        if not os.path.exists(USER_CHAT_DIR):
            os.makedirs(USER_CHAT_DIR)
    except Exception:
        pass

    if not os.path.isdir(REPO_CHAT_DIR):
        REPO_CHAT_DIR = USER_CHAT_DIR
    if not os.path.isdir(USER_CHAT_DIR):
        USER_CHAT_DIR = REPO_CHAT_DIR
    if not os.path.isdir(REPO_CHAT_DIR) or not os.path.isdir(USER_CHAT_DIR):
        print(f"Error: Failed to create {REPO_CHAT_DIR} and {USER_CHAT_DIR}", file=sys.stderr)
        sys.exit(1)

    try:
        setup_logger(os.path.join(REPO_CHAT_DIR, "error.log"))
        add_gitignore(REPO_CHAT_DIR, "*")
    except Exception as exc:
        logger.error("Failed to setup logger or add .gitignore: %s", exc)

    return REPO_CHAT_DIR, USER_CHAT_DIR


def valid_git_repo(target_dir: str, valid_urls: List[str]) -> bool:
    """
    Check if a directory is a valid Git repository and if its URL is in a list of valid URLs.

    :param target_dir: The path of the directory to check.
    :param valid_urls: A list of valid Git repository URLs.
    :return: True if the directory is a valid Git repository with a valid URL, False otherwise.
    """
    try:
        from git import InvalidGitRepositoryError, Repo
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
        from git import GitCommandError, Repo
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


def get_model_config(user_chat_dir: str, model: Optional[str] = None) -> Tuple[str, Any]:
    from devchat.config import ConfigManager

    manager = ConfigManager(user_chat_dir)
    return manager.model_config(model)
