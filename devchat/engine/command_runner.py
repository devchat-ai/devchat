"""
Run Command with a input text.
"""
import os
import sys
import json
import threading
import subprocess
from typing import List
import shlex

import openai

from devchat.utils import get_logger
from .command_parser import Command


logger = get_logger(__name__)


# Equivalent of CommandRun in Python\which executes subprocesses
class CommandRunner:
    def __init__(self, model_name: str):
        self.process = None
        self._model_name = model_name

    def _call_function_by_llm(self,
                           command_name: str,
                           command: Command,
                           history_messages: List[dict]):
        """
        command needs multi parameters, so we need parse each
        parameter by LLM from input_text
        """
        properties = {}
        required = []
        for key, value in command.parameters.items():
            properties[key] = {}
            for key1, value1 in value.dict().items():
                if key1 not in ['type', 'description', 'enum'] or value1 is None:
                    continue
                properties[key][key1] = value1
            required.append(key)

        tools = [
            {
                "type": "function",
                "function": {
                    "name": command_name,
                    "description": command.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
            }
        ]

        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", None),
            base_url=os.environ.get("OPENAI_API_BASE", None)
        )

        connection_error = ''
        for _1 in range(3):
            try:
                response = client.chat.completions.create(
                    messages=history_messages,
                    model="gpt-3.5-turbo-16k",
                    stream=False,
                    tools=tools,
                    tool_choice={"type": "function", "function": {"name": command_name}}
                )

                respose_message = response.dict()["choices"][0]["message"]
                if not respose_message['tool_calls']:
                    return None
                tool_call = respose_message['tool_calls'][0]['function']
                if tool_call['name'] != command_name:
                    return None
                parameters = json.loads(tool_call['arguments'])
                return parameters
            except (ConnectionError, openai.APIConnectionError) as err:
                connection_error = err
                continue
            except Exception as err:
                print("Exception:", err, file=sys.stderr, flush=True)
                logger.exception("Call command by LLM error: %s", err)
                return None
        print("Connect Error:", connection_error, file=sys.stderr, flush=True)
        return None


    def run_command(self,
                    command_name: str,
                    command: Command,
                    history_messages: List[dict],
                    input_text: str,
                    parent_hash: str,
                    context_contents: List[str]):
        """
        if command has parameters, then generate command parameters from input by LLM
        if command.input is "required", and input is null, then return error
        """
        if command.parameters and len(command.parameters) > 0:
            if not self._model_name.startswith("gpt-"):
                return None

            arguments = self._call_function_by_llm(command_name, command, history_messages)
            if not arguments:
                print("No valid parameters generated by LLM", file=sys.stderr, flush=True)
                return (-1, "")
            return self.run_command_with_parameters(
                command,
                {
                    "input": input_text,
                    **arguments
                },
                parent_hash,
                context_contents)

        return self.run_command_with_parameters(
            command,
            {
                "input": input_text
            },
            parent_hash,
            context_contents)


    def run_command_with_parameters(self,
                                 command: Command,
                                 parameters: dict[str, str],
                                 parent_hash: str,
                                 context_contents: List[str]):
        """
        replace $xxx in command.steps[0].run with parameters[xxx]
        then run command.steps[0].run
        """
        def pipe_reader(pipe, out_data, out_flag):
            while pipe:
                data = pipe.read(1)
                if data == '':
                    break
                out_data['out'] += data
                print(data, end='', file=out_flag, flush=True)

        try:
            # add environment variables to parameters
            if parent_hash:
                os.environ['PARENT_HASH'] = parent_hash
            if context_contents:
                os.environ['CONTEXT_CONTENTS'] = json.dumps(context_contents)
            for env_var in os.environ:
                parameters[env_var] = os.environ[env_var]
            parameters["command_python"] = os.environ['command_python']

            command_run = command.steps[0]["run"]
            # Replace parameters in command run
            for parameter in parameters:
                command_run = command_run.replace('$' + parameter, str(parameters[parameter]))

            # Run command_run
            env = os.environ.copy()
            if 'PYTHONPATH' in env:
                del env['PYTHONPATH']
            # result = subprocess.run(command_run, shell=True, env=env)
            # return result
            with subprocess.Popen(
                        shlex.split(command_run),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        env=env,
                        text=True
                    ) as process:

                stdout_data = {'out': ''}
                stderr_data = {'out': ''}

                stdout_thread = threading.Thread(
                    target=pipe_reader,
                    args=(process.stdout, stdout_data, sys.stdout))
                stderr_thread = threading.Thread(
                    target=pipe_reader,
                    args=(process.stderr, stderr_data, sys.stderr))

                stdout_thread.start()
                stderr_thread.start()

                stdout_thread.join()
                stderr_thread.join()
                exit_code = process.wait()
                return (exit_code, stdout_data["out"])
            return (-1, "")
        except Exception as err:
            print("Exception:", type(err), err, file=sys.stderr, flush=True)
            return (-1, "")
