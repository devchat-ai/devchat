"""
This module contains the main function for the DevChat CLI.
"""
import click

from devchat.utils import get_logger
from devchat._cli import log
from devchat._cli import prompt
from devchat._cli import run
from devchat._cli import topic
from devchat._cli import route

logger = get_logger(__name__)


@click.group()
def main():
    """DevChat CLI: A command-line interface for DevChat."""


main.add_command(prompt)
main.add_command(log)
main.add_command(run)
main.add_command(topic)
main.add_command(route)
