import os
import sys
from typing import Dict, List, Optional, Tuple

import oyaml as yaml

from .env_manager import EXTERNAL_ENVS, PyEnvManager
from .namespace import get_prioritized_namespace_path
from .path import COMMAND_FILENAMES
from .schema import RuntimeParameter, WorkflowConfig
from .step import WorkflowStep


class Workflow:
    TRIGGER_PREFIX = "/"
    HELP_FLAG_PREFIX = "--help"

    def __init__(self, config: WorkflowConfig):
        self._config = config

        self._runtime_param = None

    @property
    def config(self):
        return self._config

    @property
    def runtime_param(self):
        return self._runtime_param

    @staticmethod
    def parse_trigger(user_input: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Check if the user input should trigger a workflow.
        Return a tuple of (workflow_name, the input without workflow trigger).

        User input is considered a workflow trigger if it starts with the Workflow.PREFIX.
        The workflow name is the first word after the prefix.
        """
        striped = user_input.strip()
        if not striped:
            return None, user_input
        if striped[0] != Workflow.TRIGGER_PREFIX:
            return None, user_input

        workflow_name = striped.split()[0][1:]

        # remove the trigger prefix and the workflow name
        actual_input = user_input.replace(f"{Workflow.TRIGGER_PREFIX}{workflow_name}", "", 1)
        return workflow_name, actual_input

    @staticmethod
    def load(workflow_name: str) -> Optional["Workflow"]:
        """
        Load a workflow from the command.yml by name.
        A workflow name is the relative path of command.yml
        to the /workflows dir joined by "."
        e.g
        - "unit_tests": means the command file of the workflow is unit_tests/command.yml
        - "commit.en": means the command file is commit/en/command.yml
        - "pr.review.zh": means the command file is pr/review/zh/command.yml
        """
        path_parts = workflow_name.split(".")
        if len(path_parts) < 1:
            return None
        # path_parts.append(COMMAND_FILENAME)
        rel_path = os.path.join(*path_parts)

        found = False
        workflow_dir = ""
        prioritized_dirs = get_prioritized_namespace_path()
        for wf_dir in prioritized_dirs:
            for fn in COMMAND_FILENAMES:
                yaml_file = os.path.join(wf_dir, rel_path, fn)
                if os.path.exists(yaml_file):
                    workflow_dir = wf_dir
                    found = True
                    break
            if found:
                break
        if not found:
            return None

        # Load and override yaml conf in top-down order
        config_dict = {}
        for i in range(len(path_parts)):
            cur_path = os.path.join(workflow_dir, *path_parts[: i + 1])
            for fn in COMMAND_FILENAMES:
                cur_yaml = os.path.join(cur_path, fn)

                if os.path.exists(cur_yaml):
                    with open(cur_yaml, "r", encoding="utf-8") as file:
                        yaml_content = file.read()
                        cur_conf = yaml.safe_load(yaml_content)
                        cur_conf["root_path"] = cur_path

                    # convert relative path to absolute path for dependencies file
                    if cur_conf.get("workflow_python", {}).get("dependencies"):
                        rel_dep = cur_conf["workflow_python"]["dependencies"]
                        abs_dep = os.path.join(cur_path, rel_dep)
                        cur_conf["workflow_python"]["dependencies"] = abs_dep

                    config_dict.update(cur_conf)

        config = WorkflowConfig.parse_obj(config_dict)

        if config.workflow_python and config.workflow_python.env_name is None:
            # use the workflow name as the env name if not set
            config.workflow_python.env_name = workflow_name

        return Workflow(config)

    def setup(
        self,
        model_name: Optional[str],
        user_input: Optional[str],
        history_messages: Optional[List[Dict]],
        parent_hash: Optional[str],
    ):
        """
        Setup the workflow with the runtime parameters and env variables.
        """
        workflow_py = ""
        if self.config.workflow_python:
            pyconf = self.config.workflow_python
            if pyconf.env_name in EXTERNAL_ENVS:
                # Use the external python set in the user settings
                workflow_py = EXTERNAL_ENVS[pyconf.env_name].python_bin
                print(
                    "\n```Step\n# Using external Python from user settings\n",
                    flush=True,
                )
                print(f"env_name: {pyconf.env_name}")
                print(f"python_bin: {workflow_py}")
                print(
                    "\nThis Python environment's version and dependencies should be "
                    "ensured by the user to meet the requirements.",
                )
                print("\n```", flush=True)

            else:
                manager = PyEnvManager()
                workflow_py = manager.ensure(pyconf.env_name, pyconf.version, pyconf.dependencies)

        runtime_param = {
            # from user interaction
            "model_name": model_name,
            "user_input": user_input,
            "history_messages": history_messages,
            "parent_hash": parent_hash,
            # from user setting or system
            "devchat_python": sys.executable,
            "workflow_python": workflow_py,
        }

        self._runtime_param = RuntimeParameter.parse_obj(runtime_param)

    def run_steps(self) -> int:
        """
        Run the steps of the workflow.
        """
        steps = self.config.steps

        for s in steps:
            step = WorkflowStep(**s)
            result = step.run(self.config, self.runtime_param)
            return_code = result[0]
            if return_code != 0:
                # stop the workflow if any step fails
                return return_code
            print("\n\n")

        return 0

    def get_help_doc(self, user_input: str) -> str:
        """
        Get the help doc content of the workflow.
        """
        help_info = self.config.help
        help_file = None

        if isinstance(help_info, str):
            # return the only help doc
            help_file = help_info

        elif isinstance(help_info, dict):
            first = next(iter(help_info))
            default_file = help_info.get(first)
            print(f"default_file: {default_file}")

            # get language code from user input
            code = user_input.strip().removeprefix(Workflow.HELP_FLAG_PREFIX)
            code = code.removeprefix(".").strip()
            help_file = help_info.get(code, default_file)

        if not help_file:
            return ""

        help_path = os.path.join(self.config.root_path, help_file)
        if os.path.exists(help_path):
            with open(help_path, "r", encoding="utf-8") as file:
                return file.read()
        return ""

    def should_show_help(self, user_input) -> bool:
        return user_input.strip().startswith(Workflow.HELP_FLAG_PREFIX)
