import json
import os
import sys
from typing import Dict, List

from devchat._cli.utils import init_dir
from devchat.utils import get_logger

from .command_parser import Command, CommandParser
from .namespace import Namespace

logger = get_logger(__name__)


DEFAULT_MODEL = "gpt-3.5-turbo"


class CommandUtil:
    @staticmethod
    def __command_parser():
        _, user_chat_dir = init_dir()
        workflows_dir = os.path.join(user_chat_dir, "workflows")
        if not os.path.exists(workflows_dir) or not os.path.isdir(workflows_dir):
            return None

        namespace = Namespace(workflows_dir)
        commander = CommandParser(namespace)
        return commander

    @staticmethod
    def load_command(command: str):
        commander = CommandUtil.__command_parser()
        if not commander:
            return None
        return commander.parse(command)

    @staticmethod
    def load_commands() -> List[Command]:
        commander = CommandUtil.__command_parser()
        if not commander:
            return []

        command_names = commander.namespace.list_names("", True)
        commands = [(name, commander.parse(name)) for name in command_names]
        return [cmd for cmd in commands if cmd[1]]


class ToolUtil:
    @staticmethod
    def __make_function_parameters(command: Command):
        properties = {}
        required = []

        if command.parameters:
            for key, value in command.parameters.items():
                properties[key] = {}
                for key1, value1 in value.dict().items():
                    if key1 not in ["type", "description", "enum"] or value1 is None:
                        continue
                    properties[key][key1] = value1
                required.append(key)
        elif command.steps[0]["run"].find("$input") > 0:
            properties["input"] = {"type": "string", "description": "input text"}
            required.append("input")

        return properties, required

    @staticmethod
    def make_function(command: Command, command_name: str):
        properties, required = ToolUtil.__make_function_parameters(command)
        command_name = command_name.replace(".", "---")

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
            },
        }

    @staticmethod
    def select_function_by_llm(
        history_messages: List[Dict], tools: List[Dict], model: str = DEFAULT_MODEL
    ):
        import httpx
        import openai

        proxy_url = os.environ.get("DEVCHAT_PROXY", "")
        proxy_setting = (
            {"proxy": {"https://": proxy_url, "http://": proxy_url}} if proxy_url else {}
        )

        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", None),
            base_url=os.environ.get("OPENAI_API_BASE", None),
            http_client=httpx.Client(**proxy_setting, trust_env=False),
        )

        try:
            response = client.chat.completions.create(
                messages=history_messages, model=model, stream=False, tools=tools
            )

            respose_message = response.dict()["choices"][0]["message"]
            if not respose_message["tool_calls"]:
                return None
            tool_call = respose_message["tool_calls"][0]["function"]
            if tool_call["name"] != tools[0]["function"]["name"]:
                error_msg = (
                    "The LLM returned an invalid function name. "
                    f"Expected: {tools[0]['function']['name']}, "
                    f"Actual: {tool_call['name']}"
                )
                print(error_msg, file=sys.stderr, flush=True)
                return None
            return {
                "name": tool_call["name"].replace("---", "."),
                "arguments": json.loads(tool_call["arguments"]),
            }
        except (ConnectionError, openai.APIConnectionError) as err:
            print("ConnectionError:", err, file=sys.stderr, flush=True)
            return None
        except openai.APIError as err:
            print("openai APIError:", err.type, file=sys.stderr, flush=True)
            logger.exception("Call command by LLM error: %s", err)
            return None
        except Exception as err:
            print("Exception:", err, file=sys.stderr, flush=True)
            logger.exception("Call command by LLM error: %s", err)
            return None

    @staticmethod
    def _create_tool(command_name: str, command: Command) -> dict:
        properties = {}
        required = []
        if command.parameters:
            for key, value in command.parameters.items():
                properties[key] = {}
                for key1, value1 in value.dict().items():
                    if key1 not in ["type", "description", "enum"] or value1 is None:
                        continue
                    properties[key][key1] = value1
                required.append(key)
        elif command.steps[0]["run"].find("$input") > 0:
            properties["input"] = {"type": "string", "description": "input text"}
            required.append("input")

        command_name = command_name.replace(".", "---")
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
            },
        }
