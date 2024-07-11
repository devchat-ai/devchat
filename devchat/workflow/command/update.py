from pathlib import Path

import click

from devchat.workflow.path import (
    WORKFLOWS_BASE,
)
from devchat.workflow.update_util import (
    HAS_GIT,
    copy_workflows_usr,
    update_by_git,
    update_by_zip,
)


@click.command(help="Update the workflow_base dir.")
@click.option("-f", "--force", is_flag=True, help="Force update the workflows to the latest main.")
def update(force: bool):
    click.echo(f"Updating wf repo... force: {force}")
    click.echo(f"WORKFLOWS_BASE: {WORKFLOWS_BASE}")

    base_path = Path(WORKFLOWS_BASE)

    if HAS_GIT:
        updated, message = update_by_git(base_path)
    else:
        updated, message = update_by_zip(base_path)

    click.echo(f"- Updated: {updated}\n- Message: {message}")
    copy_workflows_usr()
