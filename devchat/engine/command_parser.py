import os
from typing import Dict, List, Optional

import oyaml as yaml
from pydantic import BaseModel

from .namespace import Namespace


class Parameter(BaseModel):
    type: str = "string"
    description: Optional[str] = None
    enum: Optional[List[str]] = None
    default: Optional[str] = None


class Command(BaseModel):
    description: str
    hint: Optional[str] = None
    parameters: Optional[Dict[str, Parameter]] = None
    input: Optional[str] = None
    steps: Optional[List[Dict[str, str]]] = None
    path: Optional[str] = None


class CommandParser:
    def __init__(self, namespace: Namespace):
        self.namespace = namespace

    def parse(self, name: str) -> Command:
        """
        Parse a command configuration file to JSON.

        :param name: The command name in the namespace.
        :return: The JSON representation of the command.
        """
        file_path = self.namespace.get_file(name, "command.yml")
        if not file_path:
            return None
        return parse_command(file_path)


def parse_command(file_path: str) -> Command:
    """
    Parse and validate a YAML configuration file.

    :param file_path: The path to the configuration file.
    :return: The validated configuration as a Pydantic model.
    """
    # get path from file_path, /xx1/xx2/xx3.py => /xx1/xx2
    config_dir = os.path.dirname(file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        # replace {curpath} with config_dir
        content = file.read().replace("$command_path", config_dir.replace("\\", "/"))
        config_dict = yaml.safe_load(content)
    config = Command(**config_dict)
    config.path = file_path
    return config
