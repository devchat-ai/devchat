import rich_click as click
from devchat.workflow.command.update import update
from devchat.workflow.command.list import list_cmd
from devchat.workflow.command.env import env


@click.group(
    help="CLI for devchat workflow engine."
)
def workflow():
    pass


workflow.add_command(update)
workflow.add_command(list_cmd)
workflow.add_command(env)


if __name__ == "__main__":
    workflow()
