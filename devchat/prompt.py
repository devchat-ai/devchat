from abc import ABC, abstractmethod
import hashlib
from typing import Dict, List
from devchat.message import MessageType, Message
from devchat.utils import unix_to_local_datetime


class Prompt(ABC):
    """
    A class to represent a prompt and its corresponding responses from the chat API.

    Attributes:
        _model (str): The name of the language model.
        _user_name (str): The name of the user.
        _user_email (str): The email address of the user.
        _new_messages (dict): The messages for the current round of conversation.
        _history_messages (dict): The messages for the history of conversation.
        parent (str): The parent prompt hash.
        references (List[str]): The hashes of the referenced prompts.
        _timestamp (int): The timestamp when the response was created.
        _request_tokens (int): The number of tokens used in the request.
        _response_tokens (int): The number of tokens used in the response.
        _hash (str): The hash of the prompt.
    """

    def __init__(self, model: str, user_name: str, user_email: str):
        self._model: str = model
        self._user_name: str = user_name
        self._user_email: str = user_email
        self._new_messages = {
            MessageType.INSTRUCT: [],
            'request': None,
            MessageType.CONTEXT: [],
            'response': {}
        }
        self._history_messages: Dict[str, Message] = {
            MessageType.CONTEXT: [],
            MessageType.CHAT: []
        }
        self.parent: str = None
        self.references: List[str] = []
        self._timestamp: int = None
        self._request_tokens: int = None
        self._response_tokens: int = None
        self._hash: str = None

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    @abstractmethod
    def messages(self) -> List[dict]:
        """
        List of messages in the prompt to be sent to the chat API.
        """

    @property
    def new_messages(self) -> dict:
        return self._new_messages

    @property
    def new_context(self) -> List[Message]:
        return self._new_messages[MessageType.CONTEXT]

    @property
    def request(self) -> Message:
        return self._new_messages['request']

    @property
    def response(self) -> Dict[int, Message]:
        return self._new_messages['response']

    @property
    def request_tokens(self) -> int:
        return self._request_tokens

    @property
    def response_tokens(self) -> int:
        return self._response_tokens

    @property
    def hash(self) -> str:
        return self._hash

    @abstractmethod
    def append_new(self, message_type: MessageType, content: str):
        """
        Add to the current messages of the prompt.

        Args:
            message_type (MessageType): The type of the message.
            content (str): The content of the message.
        """

    @abstractmethod
    def append_history(self, message_type: MessageType, message: Message):
        """
        Add to the history messages of the prompt.

        Args:
            message (Message): The message to add.
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

    def set_hash(self):
        """Set the hash of the prompt."""
        if not self.request or not self.response:
            raise ValueError("Prompt is incomplete for hash.")
        hash_str = self.request.content
        for response in self.response.values():
            hash_str += response.content
        self._hash = hashlib.sha1(hash_str.encode()).hexdigest()
        return self._hash

    def formatted_header(self) -> str:
        """Formatted string header of the prompt."""
        formatted_str = f"User: {self._user_name} <{self._user_email}>\n"

        local_time = unix_to_local_datetime(self._timestamp)
        formatted_str += f"Date: {local_time.strftime('%a %b %d %H:%M:%S %Y %z')}\n\n"

        return formatted_str

    def formatted_response(self, index: int) -> str:
        """Formatted response of the prompt."""
        formatted_str = self.formatted_header()

        response = self.response.get(index, None)
        if response is None or response.content is None:
            raise ValueError(f"Response {index} is incomplete.")

        formatted_str += response.content.strip() + "\n\n"
        formatted_str += f"prompt {self.hash}"

        return formatted_str

    def shortlog(self) -> List[dict]:
        """Generate a shortlog of the prompt."""
        if not self.request or not self.response:
            raise ValueError("Prompt is incomplete for shortlog.")
        logs = []
        for message in self.response.values():
            shortlog_data = {
                "user": f"{self._user_name} <{self._user_email}>",
                "date": self._timestamp,
                "context": [msg.to_dict() for msg in self.new_context],
                "request": self.request.content,
                "response": message.content,
                "hash": self.hash
            }
            logs.append(shortlog_data)
        return logs
