from dataclasses import dataclass
import json
import math
from typing import List
from devchat.prompt import Prompt
from devchat.message import Message
from devchat.utils import update_dict, message_tokens, get_logger
from .openai_message import OpenAIMessage

logger = get_logger(__name__)


@dataclass
class OpenAIPrompt(Prompt):
    """
    A class to represent a prompt and its corresponding responses from OpenAI APIs.
    """

    _id: str = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def messages(self) -> List[dict]:
        combined = []
        # Instruction
        if self._new_messages[Message.INSTRUCT]:
            combined += [msg.to_dict() for msg in self._new_messages[Message.INSTRUCT]]
        # History context
        if self._history_messages[Message.CONTEXT]:
            combined += [update_dict(msg.to_dict(), 'content',
                                     f"<context>\n{msg.content}\n</context>")
                         for msg in self._history_messages[Message.CONTEXT]]
        # History chat
        if self._history_messages[Message.CHAT]:
            combined += [msg.to_dict() for msg in self._history_messages[Message.CHAT]]
        # Request
        if self.request:
            combined += [self.request.to_dict()]
        # New context
        if self.new_context:
            combined += [update_dict(msg.to_dict(), 'content',
                                     f"<context>\n{msg.content}\n</context>")
                         for msg in self.new_context]
        return combined

    def input_messages(self, messages: List[dict]):
        state = "new_instruct"
        for message_data in messages:
            message = OpenAIMessage(**message_data)

            if state == "new_instruct":
                if message.role == "system" and not message.content.startswith("<context>"):
                    self._new_messages[Message.INSTRUCT].append(message)
                else:
                    state = "history_context"

            if state == "history_context":
                if message.role == "system" and message.content.startswith("<context>"):
                    content = message.content.replace("<context>", "").replace("</context>", "")
                    message.content = content.strip()
                    self._history_messages[Message.CONTEXT].append(message)
                else:
                    state = "history_chat"

            if state == "history_chat":
                if message.role in ("user", "assistant"):
                    self._history_messages[Message.CHAT].append(message)
                else:
                    state = "new_context"

            if state == "new_context":
                if message.role == "system" and message.content.startswith("<context>"):
                    content = message.content.replace("<context>", "").replace("</context>", "")
                    message.content = content.strip()
                    self._new_messages[Message.CONTEXT].append(message)
                else:
                    logger.warning("Invalid new context message: %s", message)

        if not self.request:
            last_user_message = self._history_messages[Message.CHAT].pop()
            if last_user_message.role == "user":
                self._new_messages["request"] = last_user_message
            else:
                logger.warning("Invalid user request: %s", last_user_message)

    def append_new(self, message_type: str, content: str,
                   available_tokens: int = math.inf) -> bool:
        if message_type not in (Message.INSTRUCT, Message.CONTEXT):
            raise ValueError(f"Current messages cannot be of type {message_type}.")
        # New instructions and context are of the system role
        message = OpenAIMessage(content, 'system')

        num_tokens = message_tokens(message.to_dict(), self.model)
        if num_tokens > available_tokens:
            return False

        self._new_messages[message_type].append(message)
        self._request_tokens += num_tokens
        return True

    def _prepend_history(self, message_type: str, message: Message,
                         token_limit: int = math.inf) -> bool:
        if message_type == Message.INSTRUCT:
            raise ValueError("History messages cannot be of type INSTRUCT.")
        num_tokens = message_tokens(message.to_dict(), self.model)
        if num_tokens > token_limit - self._request_tokens:
            return False
        self._history_messages[message_type].insert(0, message)
        self._request_tokens += num_tokens
        return True

    def prepend_history(self, prompt: 'OpenAIPrompt', token_limit: int = math.inf) -> bool:
        # Prepend the first response and the request of the prompt
        if not self._prepend_history(Message.CHAT, prompt.response[0], token_limit):
            return False
        if not self._prepend_history(Message.CHAT, prompt.request, token_limit):
            return False

        # Append the context messages of the appended prompt
        for context_message in prompt.new_context:
            if not self._prepend_history(Message.CONTEXT, context_message, token_limit):
                return False
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

        for choice in response_data['choices']:
            index = choice['index']
            if index >= len(self.response):
                self.response.extend([None] * (index - len(self.response) + 1))
            self.response[index] = OpenAIMessage(**choice['message'])
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

            if index >= len(self.response):
                self.response.extend([None] * (index - len(self.response) + 1))

            if not self.response[index]:
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
