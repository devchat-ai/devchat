import json
import os
import shlex
import shutil
import sys
from typing import List
import rich_click as click
from git import Repo, GitCommandError
from devchat._cli.utils import init_dir, handle_errors, valid_git_repo, clone_git_repo
from devchat.engine import Namespace, CommandParser, RecursivePrompter
from devchat.utils import get_logger

logger = get_logger(__name__)


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_interspersed_args": False
    },
    help="The 'command' argument is the name of the command to run or get information about.")
@click.argument('command', required=False, default='')
@click.argument('args', required=False, nargs=-1)
@click.option('--list', 'list_flag', is_flag=True, default=False,
              help='List all specified commands in JSON format.')
@click.option('--recursive', '-r', 'recursive_flag', is_flag=True, default=True,
              help='List commands recursively.')
@click.option('--update-sys', 'update_sys_flag', is_flag=True, default=False,
              help='Pull the `sys` command directory from the DevChat repository.')
def run(command: str, list_flag: bool, recursive_flag: bool, update_sys_flag: bool, args: tuple):
    """
    Operate the workflow engine of DevChat.
    """
    # Prepare args as a single string for substitution
    args_str = shlex.join(args)

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
                'https://gitee.com/devchat-ai/workflows.git',
                'https://github.com/devchat-ai/workflows.git'
            ]
            _clone_or_pull_git_repo(sys_dir, git_urls)
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
                })
            click.echo(json.dumps(commands, indent=2))
            return

        if command:
            cmd = commander.parse(command)
            if not cmd:
                click.echo(f"Error: Failed to find command: {command}", err=True)
                sys.exit(1)
            if not cmd.steps:
                prompter = RecursivePrompter(namespace)
                print(args_str)  # TODO: pass args to prompter
                click.echo(prompter.run(command))
            return


def _clone_or_pull_git_repo(target_dir: str, repo_urls: List[str]):
    """
    Clone a Git repository to a specified location, or pull it if it already exists.

    :param target_dir: The path where the repository should be cloned.
    :param repo_urls: A list of possible Git repository URLs.
    """
    if os.path.exists(target_dir):
        if valid_git_repo(target_dir, repo_urls):
            try:
                repo = Repo(target_dir)
                remote = repo.remotes.origin
                click.echo(f'Pulling {target_dir}')
                remote.pull(rebase=False)
            except GitCommandError as error:
                logger.exception("Failed to pull %s: %s", target_dir, error)
                click.echo(f'{target_dir} may have a merge conflict. Please resolve it manually.',
                           err=True)
                click.echo('You are advised not to modify the repository.', err=True)
                raise
        else:
            new_dir = target_dir + '_old'
            shutil.move(target_dir, new_dir)
            click.echo(f'{target_dir} is not a valid Git repository. Moved to {new_dir}', err=True)
            clone_git_repo(target_dir, repo_urls)
    else:
        clone_git_repo(target_dir, repo_urls)

    click.echo(f'Updated {target_dir}')
