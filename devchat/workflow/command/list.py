import json
from typing import List

import click

from devchat.utils import get_logger
from devchat.workflow.namespace import (
    WorkflowMeta,
    get_prioritized_namespace_path,
    iter_namespace,
)

logger = get_logger(__name__)


@click.command(help="List all local workflows.", name="list")
@click.option("--json", "in_json", is_flag=True, help="Output in json format.")
def list_cmd(in_json: bool):
    namespace_paths = get_prioritized_namespace_path()

    workflows: List[WorkflowMeta] = []
    visited_names = set()
    for ns_path in namespace_paths:
        ws_names, visited_names = iter_namespace(ns_path, visited_names)
        workflows.extend(ws_names)

    if not in_json:
        # print basic info
        active_count = len([workflow for workflow in workflows if workflow.active])
        total_count = len(workflows)
        click.echo(f"workflows (active/total): {active_count}/{total_count}")
        for workflow in workflows:
            click.echo(workflow)

    else:
        # convert workflows to json
        # data = [asdict(workflow) for workflow in workflows]
        data = [workflow.dict() for workflow in workflows]
        json_format = json.dumps(data)
        click.echo(json_format)
