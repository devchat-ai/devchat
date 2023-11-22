import os
from typing import List, Dict, Optional
import oyaml as yaml
from pydantic import BaseModel
from .namespace import Namespace


class Parameter(BaseModel, extra='forbid'):
    type: str
    description: Optional[str]
    enum: Optional[List[str]]
    default: Optional[str]


class Command(BaseModel, extra='forbid'):
    description: str
    hint: Optional[str]
    parameters: Optional[Dict[str, Parameter]]
    input: Optional[str]
    steps: Optional[List[Dict[str, str]]]


class CommandParser:
    def __init__(self, namespace: Namespace):
        self.namespace = namespace

    def parse(self, name: str) -> Command:
        """
        Parse a command configuration file to JSON.

        :param name: The command name in the namespace.
        :return: The JSON representation of the command.
        """
        file_path = self.namespace.get_file(name, 'command.yml')
        if not file_path:
            return None
        return parse_command(file_path)

    def parse_json(self, name: str) -> str:
        """
        Parse a command configuration file to JSON.

        :param name: The command name in the namespace.
        :return: The JSON representation of the command.
        """
        file_path = self.namespace.get_file(name, 'command.yml')
        if not file_path:
            return None
        return parse_command(file_path).json()


def parse_command(file_path: str) -> Command:
    """
    Parse and validate a YAML configuration file.

    :param file_path: The path to the configuration file.
    :return: The validated configuration as a Pydantic model.
    """
    # get path from file_path, /xx1/xx2/xx3.py => /xx1/xx2
    config_dir = os.path.dirname(file_path)

    with open(file_path, 'r', encoding='utf-8') as file:
        # replace {curpath} with config_dir
        content = file.read().replace('$command_path', config_dir)
        config_dict = yaml.safe_load(content)
    config = Command(**config_dict)
    return config
