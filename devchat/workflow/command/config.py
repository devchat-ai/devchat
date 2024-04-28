import json

from pathlib import Path
from typing import NamedTuple, List, Set, Tuple
import rich_click as click
import oyaml as yaml

from devchat.workflow.path import WORKFLOWS_BASE, WORKFLOWS_CONFIG_FILENAME


@click.command(help="Workflow configuration.", name="config")
@click.option("--json", "in_json", is_flag=True, help="Output in json format.")
def config_cmd(in_json: bool):
    
    config_path = Path(WORKFLOWS_BASE) / WORKFLOWS_CONFIG_FILENAME
    print(f"config_path: {config_path}")
    config_content = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = yaml.safe_load(f.read())

    if not in_json:
        click.echo(config_content)

    else:
        json_format = json.dumps(config_content)
        click.echo(json_format)
