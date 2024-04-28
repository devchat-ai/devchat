import json
from pathlib import Path
from typing import NamedTuple, List, Set, Tuple, Optional, Dict
from dataclasses import dataclass, asdict, field

import rich_click as click
import oyaml as yaml

from devchat.workflow.namespace import get_prioritized_namespace_path
from devchat.workflow.path import COMMAND_FILENAMES


@dataclass
class WorkflowMeta:
    name: str
    namespace: str
    active: bool
    command_conf: Dict = field(
        default_factory=dict
    )  # content of command.yml, excluding "steps" field

    def __str__(self):
        return f"{'*' if self.active else ' '} {self.name} ({self.namespace})"


def iter_namespace(
    ns_path: str, existing_names: Set[str]
) -> Tuple[List[WorkflowMeta], Set[str]]:
    """
    Get all workflows under the namespace path.

    Args:
        ns_path: the namespace path
        existing_names: the existing workflow names to check if the workflow is the first priority

    Returns:
        List[WorkflowMeta]: the workflows
        Set[str]: the updated existing workflow names
    """
    root = Path(ns_path)
    interest_files = set(COMMAND_FILENAMES)
    result = []
    unique_names = set(existing_names)
    for f in root.rglob("*"):
        if f.is_file() and f.name in interest_files:
            rel_path = f.relative_to(root)
            parts = rel_path.parts
            workflow_name = ".".join(parts[:-1])
            is_first = workflow_name not in unique_names
            unique_names.add(workflow_name)

            # load the config content from f
            with open(f, "r", encoding="utf-8") as fi:
                yaml_content = fi.read()
                command_conf = yaml.safe_load(yaml_content)
                # pop the "steps" field
                command_conf.pop("steps", None)

            workflow = WorkflowMeta(
                name=workflow_name,
                namespace=root.name,
                active=is_first,
                command_conf=command_conf,
            )
            result.append(workflow)

    return result, unique_names


@click.command(help="List all local workflows.", name="list")
@click.option("--json", "in_json", is_flag=True, help="Output in json format.")
def list_cmd(in_json: bool):
    namespace_paths = get_prioritized_namespace_path()

    workflows: List[WorkflowMeta] = []
    visited_names = set()
    for ns_path in namespace_paths:
        ws, visited_names = iter_namespace(ns_path, visited_names)
        workflows.extend(ws)

    if not in_json:
        # print basic info
        active_count = len([w for w in workflows if w.active])
        total_count = len(workflows)
        click.echo(f"workflows (active/total): {active_count}/{total_count}")
        for w in workflows:
            click.echo(w)

    else:
        # convert workflows to json
        data = [asdict(w) for w in workflows]
        json_format = json.dumps(data)
        click.echo(json_format)
