from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class MessageType(Enum):
    INSTRUCTION = "instruction"
    EXAMPLE = "example"
    CONTEXT = "context"
    RECORD = "record"


class Message(ABC):
    def __init__(self, message_type: MessageType, content: Optional[str] = None):
        if not isinstance(message_type, MessageType):
            raise ValueError("Invalid message type")
        self._type = message_type
        self._content = content

    @property
    def content(self) -> Optional[str]:
        return self._content

    @content.setter
    def content(self, value: str):
        if value == "":
            raise ValueError("Content cannot be an empty string.")
        self._content = value

    def append_content(self, value: str):
        if self._content is None:
            self._content = value
        else:
            self._content += value

    @property
    def type(self) -> MessageType:
        return self._type

    @classmethod
    @abstractmethod
    def from_dict(cls, type: MessageType, message_data: dict) -> "Message":
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass
