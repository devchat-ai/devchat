from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass


class MessageType(Enum):
    INSTRUCT = "instruct"
    CONTEXT = "context"
    CHAT = "chat"


@dataclass
class Message(ABC):
    """
    The basic unit of information in a prompt.
    """
    content: str = ""

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert the message to a dictionary.
        """

    @abstractmethod
    def stream_from_dict(self, message_data: dict) -> str:
        """
        Append to the message from a dictionary returned from a streaming chat API.
        """
