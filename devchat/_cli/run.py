import json
import os
import stat
import shutil
import sys
from typing import List, Optional

import yaml
import rich_click as click
try:
    from git import Repo, GitCommandError
except Exception:
    pass
from devchat._cli.utils import init_dir, handle_errors, valid_git_repo, clone_git_repo
from devchat._cli.utils import download_and_extract_workflow
from devchat.engine import Namespace, CommandParser, RecursivePrompter
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
           model: Optional[str], config_str: Optional[str] = None,
           auto: Optional[bool] = False):
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
                'https://gitlab.com/devchat-ai/workflows.git',
                'https://github.com/devchat-ai/workflows.git'
            ]
            zip_urls = [
                'https://gitlab.com/devchat-ai/workflows/-/archive/main/workflows-main.zip',
                'https://codeload.github.com/devchat-ai/workflows/zip/refs/heads/main'
            ]
            _clone_or_pull_git_repo(sys_dir, git_urls, zip_urls)
            return

        if list_flag:
            commands = []
            hidden_workflows = read_hidden_workflows()
            for name in namespace.list_names(command, recursive_flag):
                # check whether match item == name or item.startWiths(name + ".")
                if any(name.startswith(item + ".") or item == name for item in hidden_workflows):
                    continue
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


def create_default_config_file(config_path):
    """
    Create default configuration file with predefined hidden workflows.

    This function generates a config file at `~/.chat/workflows/config.yml`.
    The default file contains a list of workflows that are hidden by default.
    For example, it includes 'unit_tests' as a hidden workflow.
    """
    default_config = {
        'hidden_workflows': [
            'unit_tests'
            # You can add more default hidden workflows here
        ]
    }

    with open(config_path, 'w', encoding="utf-8") as file:
        yaml.dump(default_config, file)

def read_hidden_workflows():
    """
    Read the list of hidden workflows from the config.yml file.

    This function checks if the configuration file exists at the specified
    path `~/.chat/workflows/config.yml`. If it does not exist, it creates
    the default configuration file with predefined hidden workflows.

    Returns:
        list: A list containing the names of hidden workflows.
    """
    user_path = os.path.expanduser('~')
    config_path = os.path.join(user_path, '.chat', 'workflows', 'config.yml')
    
    if not os.path.exists(config_path):
        create_default_config_file(config_path)

    hidden_workflows = []
    with open(config_path, 'r', encoding="utf-8") as file:
        config = yaml.safe_load(file)
        hidden_workflows = config.get('hidden_workflows', [])

    return hidden_workflows


def __onerror(func, path, exc_info):
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
    else:
        # Re-raise the error if it's a different kind of error
        raise
    
def __make_files_writable(directory):
    """
    Recursively make all files in the directory writable.
    """
    for root, dirs, files in os.walk(directory):
        for name in files:
            filepath = os.path.join(root, name)
            if not os.access(filepath, os.W_OK):
                os.chmod(filepath, stat.S_IWUSR)
                
def _clone_or_pull_git_repo(target_dir: str, repo_urls: List[str], zip_urls: List[str]):
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
        except Exception as e:
            __make_files_writable(target_dir)
            shutil.move(target_dir, new_dir)
        try:
            shutil.move(bak_dir, target_dir)
        except Exception as e:
            __make_files_writable(bak_dir)
            shutil.move(bak_dir, target_dir)
    else:
        clone_git_repo(target_dir, repo_urls)

    click.echo(f'Updated {target_dir}')
