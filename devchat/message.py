from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message(ABC):
    """
    The basic unit of information in a prompt.
    """

    content: str = ""

    INSTRUCT = "instruct"
    CONTEXT = "context"
    FUNCTION = "function"
    CHAT = "chat"

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert the message to a dictionary.
        """

    @classmethod
    @abstractmethod
    def from_dict(cls, message_data: dict) -> "Message":
        """
        Convert the message from a dictionary.
        """

    @abstractmethod
    def stream_from_dict(self, message_data: dict) -> str:
        """
        Append to the message from a dictionary returned from a streaming chat API.
        """
