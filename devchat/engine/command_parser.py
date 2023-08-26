from typing import List, Dict, Optional
import yaml
from pydantic import BaseModel


class Parameter(BaseModel):
    type: str
    description: Optional[str]
    enum: Optional[List[str]]
    default: Optional[str]


class Command(BaseModel):
    description: str
    parameters: Optional[Dict[str, Parameter]]
    steps: Optional[List[Dict[str, str]]]


def parse_command(file_path: str) -> Command:
    """
    Parse and validate a YAML configuration file.

    :param file_path: The path to the configuration file.
    :return: The validated configuration as a Pydantic model.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        config_dict = yaml.safe_load(file)
    config = Command(**config_dict)
    return config
