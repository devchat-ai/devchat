import json
import os
import stat
import shutil
import sys
from typing import List, Optional, Tuple

import rich_click as click
from devchat._cli.utils import init_dir, handle_errors, clone_git_repo
from devchat._cli.utils import download_and_extract_workflow
from devchat.engine import Namespace, CommandParser
from devchat.utils import get_logger
from devchat._cli.router import llm_commmand

logger = get_logger(__name__)

@click.command(
    help="The 'command' argument is the name of the command to run or get information about.")
@click.argument('command', required=False, default='')
@click.option('--list', 'list_flag', is_flag=True, default=False,
              help='List all specified commands in JSON format.')
@click.option('--recursive', '-r', 'recursive_flag', is_flag=True, default=True,
              help='List commands recursively.')
@click.option('--update-sys', 'update_sys_flag', is_flag=True, default=False,
              help='Pull the `sys` command directory from the DevChat repository.')
@click.option('-p', '--parent', help='Input the parent prompt hash to continue the conversation.')
@click.option('-r', '--reference', multiple=True,
              help='Input one or more specific previous prompts to include in the current prompt.')
@click.option('-i', '--instruct', multiple=True,
              help='Add one or more files to the prompt as instructions.')
@click.option('-c', '--context', multiple=True,
              help='Add one or more files to the prompt as a context.')
@click.option('-m', '--model', help='Specify the model to use for the prompt.')
@click.option('--config', 'config_str',
              help='Specify a JSON string to overwrite the default configuration for this prompt.')
def run(command: str, list_flag: bool, recursive_flag: bool, update_sys_flag: bool,
        parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None):
    """
    Operate the workflow engine of DevChat.
    """
    _, user_chat_dir = init_dir()
    with handle_errors():
        workflows_dir = os.path.join(user_chat_dir, 'workflows')
        if not os.path.exists(workflows_dir):
            os.makedirs(workflows_dir)
        if not os.path.isdir(workflows_dir):
            click.echo(f"Error: Failed to find workflows directory: {workflows_dir}", err=True)
            sys.exit(1)

        namespace = Namespace(workflows_dir)
        commander = CommandParser(namespace)

        if update_sys_flag:
            sys_dir = os.path.join(workflows_dir, 'sys')
            git_urls = [
                ('https://gitlab.com/devchat-ai/workflows.git', 'main'),
                ('https://github.com/devchat-ai/workflows.git', 'main')
            ]
            zip_urls = [
                'https://gitlab.com/devchat-ai/workflows/-/archive/main/workflows-main.zip',
                'https://codeload.github.com/devchat-ai/workflows/zip/refs/heads/main'
            ]
            _clone_or_pull_git_repo(sys_dir, git_urls, zip_urls)
            return

        if list_flag:
            commands = []
            for name in namespace.list_names(command, recursive_flag):
                cmd = commander.parse(name)
                if not cmd:
                    logger.warning("Existing command directory failed to parse: %s", name)
                    continue
                commands.append({
                    'name': name,
                    'description': cmd.description,
                    'path': cmd.path
                })
            click.echo(json.dumps(commands, indent=2))
            return

        if command:
            llm_commmand(
                command,
                parent,
                reference,
                instruct,
                context,
                model,
                config_str
            )
            return

def __onerror(func, path, _1):
    """
    Error handler for shutil.rmtree.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : shutil.rmtree(path, onerror=onerror)
    """
    # Check if file access issue
    if not os.access(path, os.W_OK):
        # Try to change the file to be writable (remove read-only flag)
        os.chmod(path, stat.S_IWUSR)
        # Retry the function that failed
        func(path)

def __make_files_writable(directory):
    """
    Recursively make all files in the directory writable.
    """
    for root, _1, files in os.walk(directory):
        for name in files:
            filepath = os.path.join(root, name)
            if not os.access(filepath, os.W_OK):
                os.chmod(filepath, stat.S_IWUSR)

def _clone_or_pull_git_repo(target_dir: str, repo_urls: List[Tuple[str, str]], zip_urls: List[str]):
    """
    Clone a Git repository to a specified location, or pull it if it already exists.

    :param target_dir: The path where the repository should be cloned.
    :param repo_urls: A list of possible Git repository URLs.
    """
    if shutil.which('git') is None:
        # If Git is not installed, download and extract the workflow
        for url in zip_urls:
            try:
                download_and_extract_workflow(url, target_dir)
                break
            except Exception as err:
                logger.exception("Failed to download and extract workflow: %s", err)
        return

    if os.path.exists(target_dir):
        bak_dir = target_dir + '_bak'
        new_dir = target_dir + '_old'
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir, onerror=__onerror)
        if os.path.exists(bak_dir):
            shutil.rmtree(bak_dir, onerror=__onerror)
        click.echo(f'{target_dir} is already exists. Moved to {new_dir}')
        clone_git_repo(bak_dir, repo_urls)
        try:
            shutil.move(target_dir, new_dir)
        except Exception:
            __make_files_writable(target_dir)
            shutil.move(target_dir, new_dir)
        try:
            shutil.move(bak_dir, target_dir)
        except Exception:
            __make_files_writable(bak_dir)
            shutil.move(bak_dir, target_dir)
    else:
        clone_git_repo(target_dir, repo_urls)

    click.echo(f'Updated {target_dir}')
