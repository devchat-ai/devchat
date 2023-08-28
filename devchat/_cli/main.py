"""
This module contains the main function for the DevChat CLI.
"""
import importlib.metadata
import rich_click as click
from devchat.utils import get_logger
from devchat._cli import log
from devchat._cli import prompt
from devchat._cli import run
from devchat._cli import topic

logger = get_logger(__name__)
click.rich_click.USE_MARKDOWN = True


@click.group()
@click.version_option(importlib.metadata.version("devchat"), '--version',
                      message='DevChat %(version)s')
def main():
    """DevChat CLI: A command-line interface for DevChat."""


main.add_command(prompt)
main.add_command(log)
main.add_command(run)
main.add_command(topic)
