"""
Commands for managing the python environment of workflows.
"""

import sys
from pathlib import Path
from typing import List, Optional

import click

from devchat.workflow.env_manager import MAMBA_PY_ENVS, PyEnvManager


def _get_all_env_names() -> List[str]:
    """
    Get all the python env names of workflows.
    """
    # devchat reserved envs
    excludes = ["devchat", "devchat-ask", "devchat-commands"]

    envs_path = Path(MAMBA_PY_ENVS)
    envs = [env.name for env in envs_path.iterdir() if env.is_dir() and env.name not in excludes]
    return envs


@click.command(help="List all the python envs of workflows.", name="list")
def list_envs():
    envs = _get_all_env_names()
    click.echo(f"Found {len(envs)} python envs of workflows:")
    click.echo("\n".join(envs))


@click.command(help="Remove a specific workflow python env.")
@click.option(
    "--env-name",
    "-n",
    help="The name of the python env to remove.",
    required=False,
    type=str,
)
@click.option("--all", "all_flag", help="Remove all the python envs of workflows.", is_flag=True)
def remove(env_name: Optional[str] = None, all_flag: bool = False):
    if not env_name and not all_flag:
        click.echo("Please provide the name of the python env to remove.")
        sys.exit(1)

    if env_name:
        manager = PyEnvManager()
        remove_ok = manager.remove(env_name)

        if remove_ok:
            click.echo(f"Removed python env: {env_name}")
            sys.exit(0)

        else:
            click.echo(f"Failed to remove python env: {env_name}")
            sys.exit(1)

    if all_flag:
        envs = _get_all_env_names()
        manager = PyEnvManager()
        ok = []
        failed = []
        for name in envs:
            remove_ok = manager.remove(name)
            if remove_ok:
                ok.append(name)
            else:
                failed.append(name)

        click.echo(f"Removed {len(ok)} python envs of workflows:")
        click.echo("\n".join(ok))
        if failed:
            click.echo(f"Failed to remove {len(failed)} python envs of workflows:")
            click.echo("\n".join(failed))

        sys.exit(0)


@click.group(help="Manage the python environment of workflows.")
def env():
    pass


env.add_command(list_envs)
env.add_command(remove)
