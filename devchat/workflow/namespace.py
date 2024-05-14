"""
Namespace management for workflows
"""

import os
from typing import List

import oyaml as yaml
from pydantic import BaseModel, Extra, ValidationError

from devchat.utils import get_logger

from .path import (
    COMMUNITY_WORKFLOWS,
    CUSTOM_BASE,
    CUSTOM_CONFIG_FILE,
    MERICO_WORKFLOWS,
)

logger = get_logger(__name__)


class CustomConfig(BaseModel):
    namespaces: List[str] = []  # active namespaces ordered by priority

    class Config:
        extra = Extra.ignore


def _load_custom_config() -> CustomConfig:
    """
    Load the custom config file.
    """
    config = CustomConfig()

    if not os.path.exists(CUSTOM_CONFIG_FILE):
        return config

    with open(CUSTOM_CONFIG_FILE, "r", encoding="utf-8") as file:
        content = file.read()
        yaml_content = yaml.safe_load(content)
        try:
            if yaml_content:
                config = CustomConfig.parse_obj(yaml_content)
        except ValidationError as err:
            logger.warning("Invalid custom config file: %s", err)

    return config


def get_prioritized_namespace_path() -> List[str]:
    """
    Get the prioritized namespaces.

    priority: custom > merico > community
    """
    config = _load_custom_config()

    namespaces = config.namespaces

    namespace_paths = [os.path.join(CUSTOM_BASE, ns) for ns in namespaces]

    namespace_paths.append(MERICO_WORKFLOWS)
    namespace_paths.append(COMMUNITY_WORKFLOWS)

    return namespace_paths


def main():
    paths = get_prioritized_namespace_path()
    for pathv in paths:
        print(pathv)


if __name__ == "__main__":
    main()
