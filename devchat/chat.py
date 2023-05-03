from abc import ABC, abstractmethod
from typing import Iterator
from devchat.prompt import Prompt


class Chat(ABC):
    """
    Chat interface for managing chat-related interactions.

    This interface defines methods for prompting a chat system with
    a list of Message objects and retrieving responses, either as a
    complete response or as a streaming response.
    """

    @abstractmethod
    def init_prompt(self, request: str) -> Prompt:
        """
        Initialize a prompt for the chat system.

        Args:
            request (str): The basic request of the prompt.
                           The returned prompt can be combined with more instructions and context.
        """

    @abstractmethod
    def complete_response(self, prompt: Prompt) -> str:
        """
        Retrieve a complete response JSON string from the chat system.

        Args:
            prompt (Prompt): A prompt of messages representing the conversation.
        Returns:
            str: A JSON string representing the complete response.
        """

    @abstractmethod
    def stream_response(self, prompt: Prompt) -> Iterator[str]:
        """
        Retrieve a streaming response as an iterator of JSON strings from the chat system.

        Args:
            prompt (Prompt): A prompt of messages representing the conversation.
        Returns:
            Iterator[str]: An iterator over JSON strings representing the streaming response events.
        """
