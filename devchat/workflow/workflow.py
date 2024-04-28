# pylint: disable=invalid-name

import os
import sys
from typing import Optional, Tuple, List, Dict
import oyaml as yaml
from .step import WorkflowStep
from .schema import WorkflowConfig, RuntimeParameter
from .path import COMMAND_FILENAMES
from .namespace import get_prioritized_namespace_path

from .env_manager import PyEnvManager


class Workflow:
    # TODO: align args and others with the documentation

    TRIGGER_PREFIX = "="

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
        actual_input = user_input.replace(
            f"{Workflow.TRIGGER_PREFIX}{workflow_name}", "", 1
        )
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
            # TODO: 有没有更好的时机判断方法？既保证运行时一定安装了依赖、又不用每次都检查？
            # TODO: 只在插件(IDE)启动后workflow第一次使用时ensure环境和依赖？
            # Create workflow python env if set in the config
            pyconf = self.config.workflow_python

            manager = PyEnvManager()
            workflow_py = manager.ensure(pyconf.env_name, pyconf.version)

            # r_file = os.path.join(self.config.root_path, pyconf.dependencies)
            r_file = pyconf.dependencies
            # print(f"\n\n requirements file: {r_file} \n\n")
            _ = manager.install(pyconf.env_name, r_file)
            # print(f"\n\ninstall result: {p}")

        runtime_param = {
            # from user interaction
            "model_name": model_name,
            "user_input": user_input,
            "history_messages": history_messages,
            "parent_hash": parent_hash,
            # from user setting or system
            # TODO: what if the user has not set the python path?
            "devchat_python": sys.executable,
            "workflow_python": workflow_py,
        }

        self._runtime_param = RuntimeParameter.parse_obj(runtime_param)

    def run_steps(self):
        """
        Run the steps of the workflow.
        """
        steps = self.config.steps

        for s in steps:
            step = WorkflowStep(**s)
            step.run(self.config, self.runtime_param)

            print("\n\n")
