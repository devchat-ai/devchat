import json
from pathlib import Path

import click
import oyaml as yaml

from devchat.workflow.path import WORKFLOWS_BASE, WORKFLOWS_CONFIG_FILENAME


@click.command(help="Workflow configuration.", name="config")
@click.option("--json", "in_json", is_flag=True, help="Output in json format.")
def config_cmd(in_json: bool):
    config_path = Path(WORKFLOWS_BASE) / WORKFLOWS_CONFIG_FILENAME
    config_content = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as file:
            config_content = yaml.safe_load(file.read())

    if not in_json:
        click.echo(config_content)

    else:
        json_format = json.dumps(config_content)
        click.echo(json_format)
