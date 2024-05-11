"""
Namespace management for workflows
"""

import os
from typing import List
from pydantic import BaseModel, Extra, ValidationError
import oyaml as yaml
from devchat.utils import get_logger

from .path import (
    CUSTOM_BASE,
    MERICO_WORKFLOWS,
    COMMUNITY_WORKFLOWS,
    CUSTOM_CONFIG_FILE,
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

    with open(CUSTOM_CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        yaml_content = yaml.safe_load(content)
        try:
            if yaml_content:
                config = CustomConfig.parse_obj(yaml_content)
        except ValidationError as e:
            logger.warning(f"Invalid custom config file: {e}")

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
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
