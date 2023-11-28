import os
import json
from typing import List
import openai
from devchat._cli.utils import init_dir
from . import Namespace, CommandParser, Command
from .command_runner import CommandRunner


def _load_command(command: str):
    _, user_chat_dir = init_dir()
    workflows_dir = os.path.join(user_chat_dir, 'workflows')
    if not os.path.exists(workflows_dir):
        return None
    if not os.path.isdir(workflows_dir):
        return None

    namespace = Namespace(workflows_dir)
    commander = CommandParser(namespace)

    cmd = commander.parse(command)
    if not cmd:
        return None
    return cmd


def _load_commands() -> List[Command]:
    _, user_chat_dir = init_dir()
    workflows_dir = os.path.join(user_chat_dir, 'workflows')
    if not os.path.exists(workflows_dir):
        return None
    if not os.path.isdir(workflows_dir):
        return None

    namespace = Namespace(workflows_dir)
    commander = CommandParser(namespace)
    command_names = namespace.list_names("", True)

    commands = []
    for name in command_names:
        cmd = commander.parse(name)
        if not cmd:
            continue
        commands.append((name, cmd))

    return commands


def _create_tool(command_name:str, command: Command) -> dict:
    properties = {}
    required = []
    if command.parameters:
        for key, value in command.parameters.items():
            properties[key] = {}
            for key1, value1 in value.dict().items():
                if key1 not in ['type', 'description', 'enum'] or value1 is None:
                    continue
                properties[key][key1] = value1
            required.append(key)
    elif command.steps[0]['run'].find('$input') > 0:
        properties['input'] = {
            "type": "string",
            "description": "input text"
        }
        required.append('input')

    return {
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


def _create_tools() -> List[dict]:
    commands = _load_commands()
    return [_create_tool(command[0], command[1]) for command in commands if command[1].steps]


def _call_gpt(messages: List[dict],  # messages passed to GPT
              model_name: str,       # GPT model name
              use_function_calling: bool) -> dict: # whether to use function calling
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", None),
        base_url=os.environ.get("OPENAI_API_BASE", None)
    )

    tools = [] if not use_function_calling else _create_tools()

    for try_times in range(3):
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model_name,
                stream=True,
                tools=tools
            )

            response_result = {'content': None, 'function_name': None, 'parameters': ""}
            for chunk in response:
                chunk = chunk.dict()
                delta = chunk["choices"][0]["delta"]
                if 'tool_calls' in delta and delta['tool_calls']:
                    tool_call = delta['tool_calls'][0]['function']
                    if tool_call.get('name', None):
                        response_result["function_name"] = tool_call["name"]
                    if tool_call.get("arguments", None):
                        response_result["parameters"] += tool_call["arguments"]
                if delta.get('content', None):
                    if response_result["content"]:
                        response_result["content"] += delta["content"]
                    else:
                        response_result["content"] = delta["content"]
                    print(delta["content"], end='', flush=True)
            if response_result["function_name"]:
                print("``` command_run")
                function_call = {
                    'name': response_result["function_name"],
                    'arguments': response_result["parameters"]}
                print(json.dumps(function_call, indent=4))
                print("```", flush=True)
            return response_result
        except (ConnectionError, openai.APIConnectionError) as err:
            if try_times == 2:
                print("Connect Exception:", err)
                print(err.strerror)
                return {'content': None, 'function_name': None, 'parameters': ""}
            continue
        except Exception as err:
            print("Exception Error:", err)
            return {'content': None, 'function_name': None, 'parameters': ""}


def _create_messages():
    return []


def _call_function(function_name: str, parameters: str, model_name: str):
    """
    call function by function_name and parameters
    """
    parameters = json.loads(parameters)
    command_obj = _load_command(function_name)
    runner = CommandRunner(model_name)
    return runner.run_command_with_parameters(command_obj, parameters, "", [])


def _auto_function_calling(history_messages: List[dict], model_name:str):
    """
    通过function calling方式来回答当前问题。
    function最多被调用4次，必须进行最终答复。
    """
    function_call_times = 0

    response = _call_gpt(history_messages, model_name, True)
    while True:
        if response['function_name']:
            # run function
            function_call_times += 1
            print("do function calling", end='\n\n', flush=True)
            function_result = _call_function(
                response['function_name'],
                response['parameters'],
                model_name)
            history_messages.append({
                'role': 'function',
                'content': f'exit code: {function_result[0]} stdout: {function_result[1]}',
                'name': response['function_name']})
            print("after functon call.", end='\n\n', flush=True)

            # send function result to gpt
            if function_call_times < 5:
                response = _call_gpt(history_messages, model_name, True)
            else:
                response = _call_gpt(history_messages, model_name, False)
        else:
            return response


def _auto_route(history_messages, model_name:str):
    """
    select which command to run
    """
    response = _call_gpt(history_messages, model_name, True)
    if response['function_name']:
        return _call_function(
            response['function_name'],
            response['parameters'],
            model_name)
    elif not response['content']:
        return (-1, "")
    return (-1, "")


def run_command(
        model_name: str,
        history_messages: List[dict],
        input_text: str,
        parent_hash: str,
        context_contents: List[str],
        auto_fun: bool):
    """
    load command config, and then run Command
    """
    # split input_text by ' ','\n','\t'
    if len(input_text.strip()) == 0:
        return None
    if input_text.strip()[:1] != '/':
        if not (auto_fun and model_name.startswith('gpt-')):
            return None

        # response = _auto_function_calling(history_messages, model_name)
        # return response['content']
        return _auto_route(history_messages, model_name)
    else:
        commands = input_text.split()
        command = commands[0][1:]

        command_obj = _load_command(command)
        if not command_obj or not command_obj.steps:
            return None

        runner = CommandRunner(model_name)
        return runner.run_command(
            command,
            command_obj,
            history_messages,
            input_text,
            parent_hash,
            context_contents)
