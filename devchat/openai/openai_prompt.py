import json
import math
from typing import List
from devchat.prompt import Prompt
from devchat.message import MessageType, Message
from devchat.utils import update_dict, message_tokens
from .openai_message import OpenAIMessage


class OpenAIPrompt(Prompt):
    """
    A class to represent a prompt and its corresponding responses from OpenAI APIs.
    """

    def __init__(self, model: str, user_name: str, user_email: str):
        super().__init__(model, user_name, user_email)
        self._id: str = None

    @property
    def model(self) -> str:
        return self._model

    @property
    def id(self) -> str:
        return self._id

    @property
    def messages(self) -> List[dict]:
        combined = []
        # Instruction
        if self._new_messages[MessageType.INSTRUCT]:
            combined += [msg.to_dict() for msg in self._new_messages[MessageType.INSTRUCT]]
        # History context
        if self._history_messages[MessageType.CONTEXT]:
            combined += [update_dict(msg.to_dict(), 'content',
                                     f"<context>\n{msg.content}\n</context>")
                         for msg in self.new_context]
        # History chat
        if self._history_messages[MessageType.CHAT]:
            combined += [msg.to_dict() for msg
                         in reversed(self._history_messages[MessageType.CHAT])]
        # Request
        if self.request:
            combined += [self.request.to_dict()]
        # New context
        if self.new_context:
            combined += [update_dict(msg.to_dict(), 'content',
                                     f"<context>\n{msg.content}\n</context>")
                         for msg in self.new_context]
        return combined

    def append_new(self, message_type: MessageType, content: str,
                   available_tokens: int = math.inf) -> bool:
        if message_type not in (MessageType.INSTRUCT, MessageType.CONTEXT):
            raise ValueError(f"Current messages cannot be of type {message_type}.")
        message = OpenAIMessage(content, 'system')
        num_tokens = message_tokens(message.to_dict(), self.model)
        if num_tokens > available_tokens:
            return False
        self._new_messages[message_type].append(message)
        self._request_tokens += num_tokens
        return True

    def append_history(self, message_type: MessageType, message: Message,
                       available_tokens: int = math.inf) -> bool:
        if message_type == MessageType.INSTRUCT:
            raise ValueError("History messages cannot be of type INSTRUCT.")
        num_tokens = message_tokens(message.to_dict(), self.model)
        if num_tokens > available_tokens:
            return False
        self._history_messages[message_type].append(message)
        self._request_tokens += num_tokens
        return True

    def set_request(self, content: str) -> int:
        if not content.strip():
            raise ValueError("The request cannot be empty.")
        message = OpenAIMessage(content, 'user')
        self._new_messages['request'] = message
        self._request_tokens += message_tokens(message.to_dict(), self.model)

    def set_response(self, response_str: str):
        """
        Parse the API response string and set the Prompt object's attributes.

        Args:
            response_str (str): The JSON-formatted response string from the chat API.
        """
        response_data = json.loads(response_str)
        self._validate_model(response_data)
        self._timestamp_from_dict(response_data)
        self._id_from_dict(response_data)

        self._request_tokens = response_data['usage']['prompt_tokens']
        self._response_tokens = response_data['usage']['completion_tokens']

        self._new_messages['response'] = {
            choice['index']: OpenAIMessage(**choice['message'])
            for choice in response_data['choices']
        }
        self.set_hash()

    def append_response(self, delta_str: str) -> str:
        """
        Append the content of a streaming response to the existing messages.

        Args:
            delta_str (str): The JSON-formatted delta string from the chat API.

        Returns:
            str: The delta content with index 0. None when the response is over.
        """
        response_data = json.loads(delta_str)
        self._validate_model(response_data)
        self._timestamp_from_dict(response_data)
        self._id_from_dict(response_data)

        delta_content = ''
        for choice in response_data['choices']:
            delta = choice['delta']
            index = choice['index']

            if index not in self.response:
                self.response[index] = OpenAIMessage(**delta)
                if index == 0:
                    delta_content = self.formatted_header()
                    delta_content += self.response[0].content
            else:
                if index == 0:
                    delta_content = self.response[0].stream_from_dict(delta)
                else:
                    self.response[index].stream_from_dict(delta)

        return delta_content

    def _validate_model(self, response_data: dict):
        if not response_data['model'].startswith(self.model):
            raise ValueError(f"Model mismatch: expected '{self.model}', "
                             f"got '{response_data['model']}'")

    def _timestamp_from_dict(self, response_data: dict):
        if self._timestamp is None:
            self._timestamp = response_data['created']
        elif self._timestamp != response_data['created']:
            raise ValueError(f"Time mismatch: expected {self._timestamp}, "
                             f"got {response_data['created']}")

    def _id_from_dict(self, response_data: dict):
        if self._id is None:
            self._id = response_data['id']
        elif self._id != response_data['id']:
            raise ValueError(f"ID mismatch: expected {self._id}, "
                             f"got {response_data['id']}")
