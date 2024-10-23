import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import requests

from devchat.utils import get_logger, rmtree
from devchat.workflow.path import (
    CHAT_DIR,
    CUSTOM_BASE,
    WORKFLOWS_BASE_NAME,
)

HAS_GIT = False
try:
    from git import GitCommandError, InvalidGitRepositoryError, Repo
except ImportError:
    pass
else:
    HAS_GIT = True


REPO_NAME = "workflows"
DEFAULT_BRANCH = "scripts"
REPO_URLS = [
    # url, branch
    ("https://gitlab.com/devchat-ai/workflows.git", DEFAULT_BRANCH),
    ("git@github.com:devchat-ai/workflows.git", DEFAULT_BRANCH),
    ("https://github.com/devchat-ai/workflows.git", DEFAULT_BRANCH),
]
ZIP_URLS = [
    "https://gitlab.com/devchat-ai/workflows/-/archive/scripts/workflows-scripts.zip",
    "https://codeload.github.com/devchat-ai/workflows/zip/refs/heads/scripts",
]

# TODO: logger setting
logger = get_logger(__name__)


def _backup(workflow_base: Path, n: int = 5) -> Optional[Path]:
    """
    Backup the current workflow base dir to zip with timestamp under .backup.

    Args:
        n: the number of backups to keep, default 3

    Returns:
        Path: the backup zip path
    """

    if not workflow_base.exists():
        return None

    backup_dir = workflow_base.parent / ".backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_zip = backup_dir / f"{WORKFLOWS_BASE_NAME}_{timestamp}"
    shutil.make_archive(backup_zip, "zip", workflow_base)
    logger.info(f"Backup {workflow_base} to {backup_zip}")

    # keep the last n backups
    backups = sorted(backup_dir.glob(f"{WORKFLOWS_BASE_NAME}_*"), reverse=True)
    for backup in backups[n:]:
        backup.unlink()
        logger.info(f"Remove old backup {backup}")

    return backup_zip


def _download_zip_to_dir(candidate_urls: List[str], dst_dir: Path) -> bool:
    """
    Download the zip file with the first successful url
    in the candidate_urls to the target_dir.

    Args:
        candidate_urls: the list of candidate urls
        dst_dir: the dst dir of the extracted zip file, should not exist

    Returns:
        bool: True if success else False
    """
    assert not dst_dir.exists()

    download_ok = False
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)

        for url in candidate_urls:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_path = tmp_dir_path / f"{WORKFLOWS_BASE_NAME}_{timestamp}.zip"
                logger.info(f"Downloading workflow from {url} to {zip_path}")

                # Download the workflow zip file
                response = requests.get(url, stream=True, timeout=10)
                with open(zip_path, "wb") as zip_f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            zip_f.write(chunk)

                # Extract the zip file
                with zipfile.ZipFile(zip_path, "r") as zip_f:
                    zip_f.extractall(tmp_dir_path)

                # move the extracted dir to target dir
                extracted_dir = tmp_dir_path / f"{REPO_NAME}-{DEFAULT_BRANCH}"
                shutil.move(extracted_dir, dst_dir)
                logger.info(f"Extracted to {dst_dir}")

                download_ok = True
                break

            except Exception as e:
                logger.info(f"Failed to download from {url}: {e}")

    return download_ok


def _clone_repo_to_dir(candidates: List[Tuple[str, str]], dst_dir: Path) -> bool:
    """
    Clone the git repo with the first successful url
    in the candidates to the dst_dir.

    Args:
        candidates: the list of candidate git url and branch pairs.
        dst_dir: the dst dir of the cloned repo, should not exist

    Returns:
        bool: True if success else False
    """

    assert not dst_dir.exists()

    clone_ok = False
    for url, branch in candidates:
        try:
            Repo.clone_from(url, to_path=dst_dir, branch=branch)
            logger.info(f"Cloned from {url}|{branch} to {dst_dir}")
            clone_ok = True
            break
        except GitCommandError as e:
            logger.info(f"Failed to clone from  {url}|{branch}: {e}")

    return clone_ok


def update_by_zip(workflow_base: Path) -> Tuple[bool, str]:
    logger.info("Updating by zip file...")
    parent = workflow_base.parent

    if not workflow_base.exists():
        # No previous workflows, download to the workflow_base directly
        download_ok = _download_zip_to_dir(ZIP_URLS, workflow_base)
        if not download_ok:
            msg = "Failed to download from all zip urls. Please Try again later."
            logger.info(msg)
            return False, msg

        logger.info(f"Updated {workflow_base} successfully by zip.")

    else:
        # Has previous workflows, download as tmp_new
        tmp_new = parent / f"{WORKFLOWS_BASE_NAME}_new"
        if tmp_new.exists():
            rmtree(tmp_new)
            # TODO: handle error?
            # shutil.rmtree(tmp_new, onerror=__onerror)

        download_ok = _download_zip_to_dir(ZIP_URLS, tmp_new)

        if not download_ok:
            msg = "Failed to download from all zip urls. Skip update."
            logger.info(msg)
            return False, msg

        # backup the current workflows
        backup_zip = _backup(workflow_base)

        # rename the new dir to the workflow_base
        rmtree(workflow_base)
        shutil.move(tmp_new, workflow_base)

        msg = f"Updated {workflow_base} by zip. (backup: {backup_zip})"
        logger.info(msg)
        return True, msg


def update_by_git(workflow_base: Path) -> Tuple[bool, str]:
    logger.info("Updating by git...")
    parent = workflow_base.parent

    if not workflow_base.exists():
        # No previous workflows, clone to the workflow_base directly
        clone_ok = _clone_repo_to_dir(REPO_URLS, workflow_base)
        if not clone_ok:
            msg = "Failed to clone from all git urls. Please Try again later."
            logger.info(msg)
            return False, msg
        else:
            msg = f"Updated {workflow_base} by git."
            logger.info(msg)
            return True, msg

    else:
        # Has previous workflows
        repo = None
        try:
            # check if the workflow base dir is a valid git repo
            repo = Repo(workflow_base)
            head_name = repo.head.reference.name
        except InvalidGitRepositoryError:
            pass
        except Exception:
            repo = None

        if repo is None:
            # current workflow base dir is not a valid git repo
            # try to clone the new repo to tmp_new
            tmp_new = parent / f"{WORKFLOWS_BASE_NAME}_new"
            if tmp_new.exists():
                rmtree(tmp_new)

            clone_ok = _clone_repo_to_dir(REPO_URLS, tmp_new)
            if not clone_ok:
                msg = "Failed to clone from all git urls. Skip update."
                logger.info(msg)
                return False, msg

            # backup the current workflows
            backup_zip = _backup(workflow_base)

            # rename the new dir to the workflow_base
            rmtree(workflow_base)
            shutil.move(tmp_new, workflow_base)

            msg = f"Updated {workflow_base} by git. (backup: {backup_zip})"
            logger.info(msg)
            return True, msg

        # current workflow base dir is a valid git repo
        if head_name != DEFAULT_BRANCH:
            msg = (
                f"Current workflow branch is not the default one[{DEFAULT_BRANCH}]: "
                f"<{head_name}>. Skip update."
            )
            logger.info(msg)
            return False, msg

        try:
            repo.git.fetch("origin")
        except GitCommandError as e:
            msg = f"Failed to fetch from origin. Skip update. {e}"
            logger.info(msg)
            return False, msg

        local_main_hash = repo.head.commit.hexsha
        remote_main_hash = repo.commit(f"origin/{DEFAULT_BRANCH}").hexsha

        if local_main_hash == remote_main_hash:
            msg = f"Local branch is up-to-date with remote {DEFAULT_BRANCH}. Skip update."
            logger.info(msg)
            return False, msg

        try:
            # backup the current workflows
            backup_zip = _backup(workflow_base)

            # discard the local changes and force update to the latest main
            repo.git.reset("--hard", "HEAD")
            repo.git.clean("-df")
            repo.git.fetch("origin")
            repo.git.reset("--hard", f"origin/{DEFAULT_BRANCH}")

            msg = (
                f"Updated {workflow_base} from <{local_main_hash[:8]}> to"
                f" <{remote_main_hash[:8]}>. (backup: {backup_zip})"
            )
            logger.info(msg)

            return True, msg

        except GitCommandError as e:
            msg = f"Failed to update to the latest main: {e}. Skip update."
            logger.info(msg)
            return False, msg


def custom_update_by_git(workflow_base: Path, repo_urls=REPO_URLS) -> Tuple[bool, str]:
    logger.info("Updating custom by git...")
    # No previous workflows, clone to the workflow_base directly
    clone_ok = _clone_repo_to_dir(repo_urls, workflow_base)
    if not clone_ok:
        msg = "Failed to clone from all git urls. Please Try again later."
        logger.info(msg)
        return False, msg
    else:
        msg = f"Updated {workflow_base} by git."
        logger.info(msg)
        return True, msg


def copy_workflows_usr():
    """
    Copy workflows/usr to scripts/custom/usr for engine migration.
    """
    old_usr_dir = os.path.join(CHAT_DIR, "workflows", "usr")
    new_usr_dir = os.path.join(CUSTOM_BASE, "usr")

    old_exists = os.path.exists(old_usr_dir)
    new_exists = os.path.exists(new_usr_dir)

    if old_exists and not new_exists:
        shutil.copytree(old_usr_dir, new_usr_dir)
        logger.info(f"Copied {old_usr_dir} to {new_usr_dir} successfully.")
    else:
        logger.info(f"Skip copying usr dir. old exists: {old_exists}, new exists: {new_exists}.")
