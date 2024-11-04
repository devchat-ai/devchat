import re
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Extra, ValidationError, validator


class WorkflowPyConf(BaseModel):
    version: Optional[str]  # python version
    dependencies: str  # absolute path to the requirements file
    env_name: Optional[str]  # python env name, will use the workflow name if not set

    @validator("version")
    def validate_version(cls, value):
        pattern = r"^\d+\.\d+(\.\d+)?$"
        if not re.match(pattern, value):
            raise ValidationError(
                f"Invalid version format: {value}. Expected format is x.y or x.y.z"
            )
        return value


class ExternalPyConf(BaseModel):
    env_name: str  # the env_name of workflow python to act as
    python_bin: str  # the python executable path


class UserSettings(BaseModel):
    external_workflow_python: List[ExternalPyConf] = []

    class Config:
        extra = Extra.ignore


class WorkflowConfig(BaseModel):
    description: str
    root_path: str  # the root path of the workflow
    steps: List[Dict]
    input_required: bool = False  # True for required
    hint: Optional[str] = None
    workflow_python: Optional[WorkflowPyConf] = None
    help: Optional[Union[str, Dict[str, str]]] = None

    @validator("input_required", pre=True)
    def to_boolean(cls, value):
        return value.lower() == "required"

    class Config:
        extra = Extra.ignore


class RuntimeParameter(BaseModel):
    model_name: str
    devchat_python: str
    workflow_python: str = ""
    user_input: Optional[str]
    history_messages: Optional[Dict]
    parent_hash: Optional[str]

    class Config:
        extra = Extra.allow
