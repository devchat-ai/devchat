from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class MessageType(Enum):
    INSTRUCT = "instruct"
    RECORD = "record"
    CONTEXT = "context"


class Message(ABC):
    def __init__(self, message_type: MessageType, content: Optional[str] = ""):
        self._type = message_type
        self._content = content

    @property
    def type(self) -> MessageType:
        return self._type

    @property
    def content(self) -> str:
        return self._content

    @classmethod
    @abstractmethod
    def from_dict(cls, message_type: MessageType, message_data: dict) -> "Message":
        """
        Construct a Message instance from a dictionary returned from a chat API.
        """

    @abstractmethod
    def append_from_dict(self, message_data: dict) -> str:
        """
        Append to the message from a dictionary returned from a chat API.
        """

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert the Message object to a dictionary for calling a chat API.
        """
