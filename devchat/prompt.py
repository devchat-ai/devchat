from abc import ABC, abstractmethod
import hashlib
from typing import Dict, List
from devchat.message import MessageType, Message
from devchat.utils import unix_to_local_datetime


class Prompt(ABC):
    """
    A class to represent a prompt and its corresponding responses from the chat API.

    Attributes:
        _user_name (str): The name of the user.
        _user_email (str): The email address of the user.
        _request (Message): The request message.
        _messages (Dict[MessageType, Message]): The messages indexed by the message type.
        _responses (Dict[int, Message]): The responses indexed by an integer.
        _timestamp (int): The timestamp when the response was created.
        _request_tokens (int): The number of tokens used in the request.
        _response_tokens (int): The number of tokens used in the response.
        _hashes (Dict[int, str]): The hashes of the prompt indexed by the response index.
    """

    def __init__(self, user_name: str, user_email: str):
        self._user_name: str = user_name
        self._user_email: str = user_email
        self._timestamp: int = None

        self._request: Message = None
        self._messages: Dict[MessageType, Message] = {}
        self._responses: Dict[int, Message] = {}

        self._request_tokens: int = None
        self._response_tokens: int = None
        self._hashes: Dict[int, str] = {}

    @property
    def user_name(self) -> str:
        return self._user_name

    @property
    def user_email(self) -> str:
        return self._user_email

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    @abstractmethod
    def messages(self) -> List[dict]:
        pass

    @property
    def responses(self) -> Dict[int, Message]:
        return self._responses

    @property
    def request_tokens(self) -> int:
        return self._request_tokens

    @property
    def response_tokens(self) -> int:
        return self._response_tokens

    @property
    def hashes(self) -> Dict[int, str]:
        return self._hashes

    @abstractmethod
    def append_message(self, message_type: MessageType, content: str):
        """
        Append a message to the prompt.

        Args:
            message_type (MessageType): The type of the message. It cannot be RECORD.
            content (str): The content of the message.
        """

    @abstractmethod
    def set_request(self, content: str):
        """
        Set the request message for the prompt.

        Args:
            content (str): The request content to set.
        """

    @abstractmethod
    def set_response(self, response_str: str):
        """
        Parse the API response string and set the Prompt object's attributes.

        Args:
            response_str (str): The JSON-formatted response string from the chat API.
        """

    @abstractmethod
    def append_response(self, delta_str: str) -> str:
        """
        Append the content of a streaming response to the existing messages.

        Args:
            delta_str (str): The JSON-formatted delta string from the chat API.

        Returns:
            str: The delta content with index 0. None when the response is over.
        """

    def formatted_header(self) -> str:
        """Formatted string header of the prompt."""
        formatted_str = f"User: {self._user_name} <{self._user_email}>\n"

        local_time = unix_to_local_datetime(self._timestamp)
        formatted_str += f"Date: {local_time.strftime('%a %b %d %H:%M:%S %Y %z')}\n\n"

        return formatted_str

    def formatted_response(self, index: int) -> str:
        """Formatted response of the prompt."""
        formatted_str = self.formatted_header()

        response = self._responses.get(index, None)
        if response is None or response.content is None:
            raise ValueError(f"Response {index} is incomplete.")

        formatted_str += response.content.strip() + "\n\n"
        formatted_str += f"prompt {self.hash(index)}"

        return formatted_str

    def hash(self, index: int) -> str:
        """Hash the prompt with the response at the given index."""
        message = self._responses[index]
        message_hash = hashlib.sha1(message.content.encode()).hexdigest()
        return message_hash

    def shortlog(self) -> List[dict]:
        """Generate a shortlog of the prompt."""
        if not self._request_message or not self._responses:
            raise ValueError("Prompt is incomplete.")
        logs = []
        for index, response in self._responses.items():
            shortlog_data = {
                "user": f'{self._user_name} <{self._user_email}>',
                "date": self._timestamp,
                "last_message": self._request_message.content,
                "response": response.content,
                "hash": self.hash(index)
            }
            logs.append(shortlog_data)
        return logs
