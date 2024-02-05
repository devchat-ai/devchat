"""
Run Command with a input text.
"""
import os
import sys
import json
import threading
import subprocess
from typing import List, Dict
import shlex

import openai
from devchat.openai.openai_chat import OpenAIChatConfig

from devchat.utils import get_logger
from .command_parser import Command


logger = get_logger(__name__)


def pipe_reader(pipe, out_data, out_flag):
    while pipe:
        data = pipe.read(1)
        if data == '':
            break
        out_data['out'] += data
        print(data, end='', file=out_flag, flush=True)


def init_env_and_parameters(
        model_name: str,
        parent_hash: str,
        history_messages: List[Dict],
        command_name: str,
        parameters: Dict[str, str]):
    if model_name:
        os.environ['LLM_MODEL'] = model_name
    if parent_hash:
        os.environ['PARENT_HASH'] = parent_hash
    if history_messages:
        os.environ['CONTEXT_CONTENTS'] = json.dumps(history_messages)
    for env_var in os.environ:
        parameters[env_var] = os.environ[env_var]

    # how to get command_python path?
    root_command_name = command_name.split('.')[0]
    command_runtime = \
        os.path.expanduser(f'~/.chat/workflows/usr/{root_command_name}/runtime.json')
    if os.path.exists(command_runtime):
        with open(command_runtime, 'r', encoding='utf8') as fp:
            command_runtime_json = json.loads(fp.read())
            if 'command_python' in command_runtime_json:
                parameters['command_python'] = \
                    command_runtime_json['command_python'].replace('\\', '/')
    elif os.environ.get('command_python', None):
        parameters['command_python'] = os.environ['command_python'].replace('\\', '/')
    parameters["devchat_python"] = sys.executable.replace('\\', '/')


# Equivalent of CommandRun in Python\which executes subprocesses
class CommandRunner:
    def __init__(self, model_name: str):
        self.process = None
        self._model_name = model_name

    def _call_function_by_llm(self,
                           openai_config: OpenAIChatConfig,
                           command_name: str,
                           command: Command,
                           history_messages: List[Dict]):
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

        command_name = command_name.replace('.', '---')
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

        config_params = openai_config.dict(exclude_unset=True)
        config_params.pop('stream', None)
        config_params.pop('user', None)
        config_params.pop('request_timeout', None)
        config_params.pop('model', None)

        connection_error = ''
        for _1 in range(3):
            try:
                response = client.chat.completions.create(
                    messages=history_messages,
                    model="gpt-3.5-turbo-16k",
                    stream=False,
                    **config_params,
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
                    openai_config: OpenAIChatConfig,
                    command_name: str,
                    command: Command,
                    history_messages: List[Dict],
                    input_text: str,
                    parent_hash: str):
        """
        if command has parameters, then generate command parameters from input by LLM
        if command.input is "required", and input is null, then return error
        """
        input_text = input_text.strip()\
                    .replace(f'/{command_name}', '')\
                    .replace('\"', '\\"')\
                    .replace('\'', '\\\'')\
                    .replace('\n', '\\n')
        if command.parameters and len(command.parameters) > 0:
            if not self._model_name.startswith("gpt-"):
                return None

            arguments = self._call_function_by_llm(
                openai_config, command_name, command, history_messages
            )
            if not arguments:
                print("No valid parameters generated by LLM", file=sys.stderr, flush=True)
                return (-1, "")
            return self.run_command_with_parameters(
                command_name,
                command,
                {
                    "input": input_text,
                    **arguments
                },
                parent_hash,
                history_messages)


        return self.run_command_with_parameters(
            command_name,
            command,
            {
                "input": input_text
            },
            parent_hash,
            history_messages)


    def run_command_with_parameters(self,
                                 command_name: str,
                                 command: Command,
                                 parameters: Dict[str, str],
                                 parent_hash: str,
                                 history_messages: List[Dict]):
        """
        replace $xxx in command.steps[0].run with parameters[xxx]
        then run command.steps[0].run
        """
        

        try:
            # add environment variables to parameters
            init_env_and_parameters(
                self._model_name, parent_hash, history_messages,
                command_name, parameters
            )

            command_run = command.steps[0]["run"]

            # if $devchat_python in command_run
            # then set environ PYTHONPATH to DEVCHAT_PYTHONPATH
            # if command_python in command_run
            # then unset environ PYTHONPATH
            env = os.environ.copy()
            if 'DEVCHAT_PYTHONPATH' not in env:
                env['DEVCHAT_PYTHONPATH'] = os.environ.get('PYTHONPATH', '')
            if command_run.find('$devchat_python ') == -1:
                del env['PYTHONPATH']
            if (
                    command_run.find('$command_python ') != -1 
                    and parameters.get('command_python', '') == ''
                ):
                error_msg = ('devchat-commands environment is not installed yet. '
                             'Please install it before using the current command.'
                             'The devchat-command environment is automatically '
                             'installed after the plugin starts,'
                             ' and details can be viewed in the output window.')
                print(error_msg, file=sys.stderr, flush=True)
                return (-1, "")

            # Replace parameters in command run
            for parameter in parameters:
                command_run = command_run.replace('$' + parameter, str(parameters[parameter]))
            # Check whether there is parameter not specified
            has_parameter = command_run.find('$') != -1
            is_input_required = command.input == "required"
            is_input_invalid = (is_input_required and parameters["input"] == "")
            if has_parameter or is_input_invalid:
                command_dir = os.path.dirname(command.path)
                readme_file = os.path.join(command_dir, 'README.md')
                if os.path.exists(readme_file):
                    with open(readme_file, 'r', encoding='utf8') as fp:
                        readme = fp.read()
                    print(readme, flush=True)
                    return (0, readme)
                if has_parameter:
                    print(
                        "Missing argument. the command being parsed is:",
                        command_run, file=sys.stderr, flush=True)
                else:
                    print(
                        ("Missing input which is required. You can use it as "
                            f"'/{command_name} some related description'"),
                        file=sys.stderr, flush=True)
                return (-1, "")

            # result = subprocess.run(command_run, shell=True, env=env)
            # return result
            # command_run = command_run.replace('\\', '/')
            with subprocess.Popen(
                        shlex.split(command_run),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
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
