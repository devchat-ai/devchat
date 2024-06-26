import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import click
from devchat.workflow.path import (
    WORKFLOWS_BASE,
)
from devchat.workflow.update_util import (
    update_by_git,
    update_by_zip,
    HAS_GIT,
    copy_workflows_usr,
)

@click.command(help="Update the workflow_base dir.")
@click.option(
    "-f", "--force", is_flag=True, help="Force update the workflows to the latest main."
)
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
