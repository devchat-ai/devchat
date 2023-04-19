from typing import List, Iterator
from devchat.message import Message

class Chat:
    """
    Chat interface for managing chat-related interactions.

    This interface defines methods for prompting a chat system with
    a list of Message objects and retrieving responses, either as a
    complete response or as a streamed response.
    """

    def prompt(self, messages: List[Message]) -> None:
        """Send a list of Message objects as a prompt to the chat system."""
        raise NotImplementedError()

    def complete_response(self) -> str:
        """
        Retrieve a complete response JSON string from the chat system.

        Returns:
            str: A JSON string representing the complete response from the chat system.
        """
        raise NotImplementedError()

    def stream_response(self) -> Iterator[str]:
        """
        Retrieve a streamed response as an iterator of JSON strings from the chat system.

        Returns:
            Iterator[str]: An iterator over JSON strings representing the streamed response
                           events from the chat system.
        """
        raise NotImplementedError()
