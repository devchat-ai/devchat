import json
import os
import shlex
import subprocess
import sys
import threading
from enum import Enum
from typing import Dict, List, Tuple

from .path import WORKFLOWS_BASE
from .schema import RuntimeParameter, WorkflowConfig


class BuiltInVars(str, Enum):
    """
    Built-in variables within the workflow step command.
    """

    devchat_python = "$devchat_python"
    command_path = "$command_path"
    user_input = "$input"
    workflow_python = "$workflow_python"


class BuiltInEnvs(str, Enum):
    """
    Built-in environment variables for the step subprocess.
    """

    llm_model = "LLM_MODEL"
    parent_hash = "PARENT_HASH"
    context_contents = "CONTEXT_CONTENTS"


class WorkflowStep:
    def __init__(self, **kwargs):
        """
        Initialize a workflow step with the given configuration.
        """
        self._kwargs = kwargs

    @property
    def command_raw(self) -> str:
        """
        The raw command string from the config.
        """
        return self._kwargs.get("run", "")

    def _setup_env(self, wf_config: WorkflowConfig, rt_param: RuntimeParameter) -> Dict[str, str]:
        """
        Setup the environment variables for the subprocess.
        """
        _1 = wf_config
        command_raw = self.command_raw

        env = os.environ.copy()

        # set PYTHONPATH for the subprocess
        python_path = env.get("PYTHONPATH", "")
        devchat_python_path = env.get("DEVCHAT_PYTHONPATH", python_path)
        new_paths = [WORKFLOWS_BASE]
        if (BuiltInVars.devchat_python in command_raw) and devchat_python_path:
            # only add devchat pythonpath when it's used in the command
            new_paths.append(devchat_python_path)

        paths = [os.path.normpath(p) for p in new_paths]
        paths = [p.replace("\\", "\\\\") for p in paths]
        joined = os.pathsep.join(paths)

        env["PYTHONPATH"] = joined
        env[BuiltInEnvs.llm_model] = rt_param.model_name or ""
        env[BuiltInEnvs.parent_hash] = rt_param.parent_hash or ""
        env[BuiltInEnvs.context_contents] = ""
        if rt_param.history_messages:
            # convert dict to json string
            env[BuiltInEnvs.context_contents] = json.dumps(rt_param.history_messages)

        return env

    def _validate_and_interpolate(
        self, wf_config: WorkflowConfig, rt_param: RuntimeParameter
    ) -> List[str]:
        """
        Validate the step configuration and interpolate variables in the command.

        Return the command parts as a list of strings.
        """
        command_raw = self.command_raw
        parts = shlex.split(command_raw)

        # if the command_raw use $workflow_python,
        # it must be set in workflow config
        if BuiltInVars.workflow_python in command_raw:
            if not rt_param.workflow_python:
                raise ValueError(
                    "The command uses $workflow_python, " "but the workflow_python is not set yet."
                )

        args = []
        for p in parts:
            arg = p

            if p.startswith(BuiltInVars.workflow_python):
                if not rt_param.workflow_python:
                    raise ValueError(
                        "The command uses $workflow_python, "
                        "but the workflow_python is not set yet."
                    )
                arg = arg.replace(BuiltInVars.workflow_python, rt_param.workflow_python)

            if p.startswith(BuiltInVars.devchat_python):
                arg = arg.replace(BuiltInVars.devchat_python, rt_param.devchat_python)

            if p.startswith(BuiltInVars.command_path):
                # NOTE: 在文档中说明 command.yml 中表示路径采用 POSIX 标准
                # 即，使用 / 分隔路径，而非 \ (Windows)
                path_parts = p.split("/")
                # replace "$command_path" with the root path in path_parts
                arg = os.path.join(wf_config.root_path, *path_parts[1:])

            if BuiltInVars.user_input in p:
                arg = arg.replace(BuiltInVars.user_input, rt_param.user_input)

            args.append(arg)

        return args

    def run(self, wf_config: WorkflowConfig, rt_param: RuntimeParameter) -> Tuple[int, str, str]:
        """
        Run the step in a subprocess.

        Returns the return code, stdout, and stderr.
        """
        # setup the environment variables
        env = self._setup_env(wf_config, rt_param)

        command_args = self._validate_and_interpolate(wf_config, rt_param)

        def _pipe_reader(pipe, data, out_file):
            """
            Read from the pipe, then write and save the data.
            """
            while pipe:
                pipe_data = pipe.read(1)
                if pipe_data == "":
                    break
                data["data"] += pipe_data
                print(pipe_data, end="", file=out_file, flush=True)

        with subprocess.Popen(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        ) as proc:
            stdout_data, stderr_data = {"data": ""}, {"data": ""}
            stdout_thread = threading.Thread(
                target=_pipe_reader, args=(proc.stdout, stdout_data, sys.stdout)
            )
            stderr_thread = threading.Thread(
                target=_pipe_reader, args=(proc.stderr, stderr_data, sys.stderr)
            )
            stdout_thread.start()
            stderr_thread.start()
            stdout_thread.join()
            stderr_thread.join()

            proc.wait()
            return_code = proc.returncode
            return return_code, stdout_data["data"], stderr_data["data"]
