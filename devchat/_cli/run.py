import json
import os
import sys
import rich_click as click
from devchat._cli.utils import init_dir, handle_errors
from devchat.engine import Namespace, CommandParser, RecursivePrompter
from devchat.utils import get_logger

logger = get_logger(__name__)


@click.command(
    help="The 'command' argument is the name of the command to run or get information about.")
@click.argument('command', required=False, default='')
@click.option('--list', 'list_flag', is_flag=True, default=False,
              help='List all commands in JSON format.')
@click.option('--recursive', '-r', 'recursive_flag', is_flag=True, default=True,
              help='List all commands recursively.')
def run(command: str, list_flag: bool, recursive_flag: bool):  
    """
    Operate workflow engine of DevChat.
    """
    _, _, user_chat_dir = init_dir()
    with handle_errors():
        workflows_dir = os.path.join(user_chat_dir, 'workflows')
        if not os.path.exists(workflows_dir):
            os.makedirs(workflows_dir)
        if not os.path.isdir(workflows_dir):
            click.echo(f"Error: Failed to find workflows directory: {workflows_dir}", err=True)
            sys.exit(1)

        namespace = Namespace(workflows_dir)
        commander = CommandParser(namespace)

        if list_flag:
            names = namespace.list_names(command, recursive_flag)
            commands = []
            for name in names:
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
                click.echo(prompter.run(command))
            return
