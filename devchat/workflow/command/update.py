# pylint: disable=invalid-name

import shutil
import tempfile
import zipfile
from typing import List, Optional, Tuple
from pathlib import Path
from datetime import datetime

import rich_click as click
import requests

from devchat.workflow.path import WORKFLOWS_BASE, WORKFLOWS_BASE_NAME
from devchat.utils import get_logger

HAS_GIT = False
try:
    from git import Repo, InvalidGitRepositoryError, GitCommandError
except ImportError:
    pass
else:
    HAS_GIT = True
    # pass

# REPO_NAME = "new_workflows"
# DEFAULT_BRANCH = "main"
# REPO_URLS = [
#     # url, branch
#     ("git@github.com:kagami-l/new_workflows.git", DEFAULT_BRANCH),
# ]
# ZIP_URLS = [
#     "https://codeload.github.com/kagami-l/new_workflows/zip/refs/heads/main",
# ]

REPO_NAME = "workflows"
DEFAULT_BRANCH = "scripts"
REPO_URLS = [
    # url, branch
    ("git@github.com:devchat-ai/workflows.git", DEFAULT_BRANCH),
    ("https://github.com/devchat-ai/workflows.git", DEFAULT_BRANCH),
]
ZIP_URLS = [
    "https://codeload.github.com/devchat-ai/workflows/zip/refs/heads/scripts",
]


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
        return

    backup_dir = workflow_base.parent / ".backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_zip = backup_dir / f"{WORKFLOWS_BASE_NAME}_{timestamp}"
    shutil.make_archive(backup_zip, "zip", workflow_base)
    click.echo(f"Backup {workflow_base} to {backup_zip}")

    # keep the last n backups
    backups = sorted(backup_dir.glob(f"{WORKFLOWS_BASE_NAME}_*"), reverse=True)
    for backup in backups[n:]:
        backup.unlink()
        click.echo(f"Remove old backup {backup}")

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
                click.echo(f"Downloading workflow from {url} to {zip_path}")

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
                # TODO: use workflows-main for dev
                # TODO: will set to the actual zip dir name when the new repo is ready
                extracted_dir = (
                    tmp_dir_path / f"{REPO_NAME}-{DEFAULT_BRANCH}"
                )  # TODO: use Constant
                shutil.move(extracted_dir, dst_dir)
                click.echo(f"Extracted to {dst_dir}")

                download_ok = True
                break

            except Exception as e:
                click.echo(f"Failed to download from {url}: {e}")

    return download_ok


def update_by_zip(workflow_base: Path):
    """
    # TODO: should return the message to user? or just print/echo?
    """
    click.echo("Updating by zip file...")
    parent = workflow_base.parent

    if not workflow_base.exists():
        # No previous workflows, download to the workflow_base directly
        download_ok = _download_zip_to_dir(ZIP_URLS, workflow_base)
        if not download_ok:
            click.echo("Failed to download from all zip urls. Please Try again later.")
            return

        click.echo(f"Updated {workflow_base} successfully by zip.")

    else:
        # Has previous workflows, download as tmp_new
        tmp_new = parent / f"{WORKFLOWS_BASE_NAME}_new"
        if tmp_new.exists():
            shutil.rmtree(tmp_new)
            # TODO: handle error?
            # shutil.rmtree(tmp_new, onerror=__onerror)

        download_ok = _download_zip_to_dir(ZIP_URLS, tmp_new)

        if not download_ok:
            click.echo("Failed to download from all zip urls. Skip update.")
            return

        # backup the current workflows
        backup_zip = _backup(workflow_base)

        # rename the new dir to the workflow_base
        # TODO: handle error?
        shutil.rmtree(workflow_base)
        shutil.move(tmp_new, workflow_base)

        click.echo(f"Updated {workflow_base} by zip. (backup: {backup_zip})")


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
            # TODO: What will happen when using an SSH URL without configuring an SSH key
            # TODO：how to handle it?
            repo = Repo.clone_from(url, to_path=dst_dir, branch=branch)
            click.echo(f"Cloned from {url}|{branch} to {dst_dir}")
            clone_ok = True
            break
        except GitCommandError as e:
            click.echo(f"Failed to clone from  {url}|{branch}: {e}")

    return clone_ok


def update_by_git(workflow_base: Path):
    """
    # TODO: should return the message to user? or just print/echo?
    """
    click.echo("Updating by git...")
    parent = workflow_base.parent

    if not workflow_base.exists():
        # No previous workflows, clone to the workflow_base directly
        clone_ok = _clone_repo_to_dir(REPO_URLS, workflow_base)
        if not clone_ok:
            click.echo("Failed to clone from all git urls. Please Try again later.")
            return

        click.echo(f"Updated {workflow_base} by git.")

    else:
        # Has previous workflows
        repo = None
        try:
            # check if the workflow base dir is a valid git repo
            repo = Repo(workflow_base)
        except InvalidGitRepositoryError:
            pass

        if repo is None:
            # current workflow base dir is not a valid git repo
            # try to clone the new repo to tmp_new
            tmp_new = parent / f"{WORKFLOWS_BASE_NAME}_new"
            if tmp_new.exists():
                shutil.rmtree(tmp_new)

            clone_ok = _clone_repo_to_dir(REPO_URLS, tmp_new)
            if not clone_ok:
                click.echo("Failed to clone from all git urls. Skip update.")
                return

            # backup the current workflows
            backup_zip = _backup(workflow_base)

            # rename the new dir to the workflow_base
            shutil.rmtree(workflow_base)
            shutil.move(tmp_new, workflow_base)
            click.echo(f"Updated {workflow_base} by git. (backup: {backup_zip})")
            return

        # current workflow base dir is a valid git repo
        head_name = repo.head.reference.name
        if head_name != DEFAULT_BRANCH:
            click.echo(
                f"Current workflow branch is not the default one[{DEFAULT_BRANCH}]: "
                f"<{head_name}>. Skip update."
            )
            return

        try:
            repo.git.fetch("origin")
        except GitCommandError as e:
            click.echo(f"Failed to fetch from origin. Skip update. {e}")
            return

        local_main_hash = repo.head.commit.hexsha
        remote_main_hash = repo.commit(f"origin/{DEFAULT_BRANCH}").hexsha

        if local_main_hash == remote_main_hash:
            click.echo(
                f"Local branch is up-to-date with remote {DEFAULT_BRANCH}. Skip update."
            )
            return

        try:
            # backup the current workflows
            backup_zip = _backup(workflow_base)

            # discard the local changes and force update to the latest main
            repo.git.reset("--hard", "HEAD")
            repo.git.clean("-df")
            repo.git.fetch("origin")
            repo.git.reset("--hard", f"origin/{DEFAULT_BRANCH}")
            click.echo(
                f"Updated {workflow_base} from <{local_main_hash[:8]}> to"
                f" <{remote_main_hash[:8]}>. (backup: {backup_zip})"
            )
        except GitCommandError as e:
            click.echo(f"Failed to update to the latest main: {e}. Skip update.")
            return
        return


@click.command(help="Update the workflow_base dir.")
@click.option(
    "-f", "--force", is_flag=True, help="Force update the workflows to the latest main."
)
def update(force: bool):
    click.echo(f"Updating wf repo... force: {force}")
    click.echo(f"WORKFLOWS_BASE: {WORKFLOWS_BASE}")

    base_path = Path(WORKFLOWS_BASE)
    # # backup(base_path)

    if HAS_GIT:
        update_by_git(base_path)
    else:
        update_by_zip(base_path)
