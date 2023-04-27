from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class MessageType(Enum):
    INSTRUCTION = "instruction"
    EXAMPLE = "example"
    CONTEXT = "context"


class Message(ABC):
    def __init__(self, message_type: MessageType, content: Optional[str] = None):
        self._content = content
        self._type = message_type

    @property
    def content(self) -> Optional[str]:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        if value == "":
            raise ValueError("Content cannot be an empty string.")
        self._content = value

    def append_content(self, value: str) -> None:
        if self._content is None:
            self._content = value
        else:
            self._content += value

    @property
    def type(self) -> MessageType:
        return self._type

    @abstractmethod
    def to_dict(self) -> dict:
        pass
