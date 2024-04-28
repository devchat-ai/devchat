import re
from typing import Optional, List, Dict

from pydantic import BaseModel, validator, Extra, ValidationError


class WorkflowPyConf(BaseModel):
    version: str  # python version
    dependencies: str  # absolute path to the requirements file
    env_name: Optional[str]  # python env name, will use the workflow name if not set

    @validator("version")
    def validate_version(cls, value):  # pylint: disable=no-self-argument
        pattern = r"^\d+\.\d+(\.\d+)?$"
        if not re.match(pattern, value):
            raise ValidationError(
                f"Invalid version format: {value}. Expected format is x.y or x.y.z"
            )
        return value


class WorkflowConfig(BaseModel):
    description: str
    root_path: str  # the root path of the workflow
    steps: List[Dict]
    input_required: bool = False  # True for required
    hint: Optional[str] = None
    workflow_python: Optional[WorkflowPyConf] = None

    @validator("input_required", pre=True)
    def to_boolean(cls, value):  # pylint: disable=no-self-argument
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
