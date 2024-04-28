"""
This module contains the main function for the DevChat CLI.
"""
import argparse
from devchat.utils import get_logger
from devchat._cli import log
from devchat._cli import prompt
from devchat._cli import run
from devchat._cli import topic
from devchat._cli import route
from devchat._cli import commands

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="CLI tool")
    subparsers = parser.add_subparsers(help='sub-command help')
    for _1, cmd in commands.items():
        cmd.register(subparsers)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        func_args = vars(args).copy()
        del func_args['func']

        args.func(**func_args)
    else:
        parser.print_help()
