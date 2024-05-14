import click

from devchat.workflow.command.config import config_cmd
from devchat.workflow.command.env import env
from devchat.workflow.command.list import list_cmd
from devchat.workflow.command.update import update


@click.group(help="CLI for devchat workflow engine.")
def workflow():
    pass


workflow.add_command(update)
workflow.add_command(list_cmd)
workflow.add_command(env)
workflow.add_command(config_cmd)


if __name__ == "__main__":
    workflow()
