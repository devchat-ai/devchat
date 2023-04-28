from abc import ABC, abstractmethod
import hashlib
from typing import Dict, List
from devchat.message import Message, MessageType
from devchat.utils import unix_to_local_datetime


class Prompt(ABC):
    """
    A class to represent a prompt and its corresponding responses from the chat API.

    Attributes:
        model (str): The model used for the chat API request, e.g., "gpt-3.5-turbo".
        user_name (str): The name of the user.
        user_email (str): The email address of the user.
        messages (List[Message]): The messages in the prompt.
        responses (Dict[int, Message]): The responses indexed by an integer.
        time (int): The timestamp when the response was created.
        request_tokens (int): The number of tokens used in the request.
        response_tokens (int): The number of tokens used in the response.
    """

    def __init__(self, model: str, user_name: str, user_email: str):
        self.model: str = model
        self.user_name: str = user_name
        self.user_email: str = user_email
        self.messages: List[Message] = []
        self.responses: Dict[int, Message] = {}
        self.time: int = None
        self.request_tokens: int = None
        self.response_tokens: int = None

    @abstractmethod
    def append_message(self, type: MessageType, content: str):
        """
        Append a message to the prompt.

        Args:
            message (Message): The message to append.
        """
        pass

    @abstractmethod
    def set_response(self, response_str: str):
        """
        Parse the API response string and set the Prompt object's attributes.

        Args:
            response_str (str): The JSON-formatted response string from the chat API.
        """
        pass

    @abstractmethod
    def append_response(self, delta_str: str) -> str:
        """
        Append the content of a streaming response to the existing messages.

        Args:
            delta_str (str): The JSON-formatted delta string from the chat API.

        Returns:
            str: The delta content with index 0. None when the response is over.
        """
        pass

    def formatted_header(self) -> str:
        formatted_str = f"User: {self.user_name} <{self.user_email}>\n"

        dt = unix_to_local_datetime(self.response_time)
        formatted_str += f"Date: {dt.strftime('%a %b %d %H:%M:%S %Y %z')}\n\n"

        return formatted_str

    def formatted_response(self, index: int) -> str:
        formatted_str = self.formatted_header()

        response = self.responses.get(index, None)
        if response is None or response.content is None:
            raise ValueError(f"Response {index} is incomplete.")

        formatted_str += response.content.strip() + "\n\n"
        formatted_str += f"prompt {self.hash(index)}"

        return formatted_str

    def hash(self, index: int) -> str:
        message = self.responses[index]
        message_hash = hashlib.sha1(message.content.encode()).hexdigest()
        return message_hash

    def shortlog(self) -> List[dict]:
        if not self.messages or not self.responses:
            raise ValueError("Prompt is incomplete.")
        logs = []
        for index, response in self.responses.items():
            shortlog_data = {
                "user": f'{self.user_name} <{self.user_email}>',
                "date": self.time,
                "last_message": self.messages[-1].content,
                "response": response.content,
                "hash": self.hash(index)
            }
            logs.append(shortlog_data)
        return logs
