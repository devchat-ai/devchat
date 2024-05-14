import json
import sys
from dataclasses import dataclass
from typing import List, Optional

from devchat.message import Message
from devchat.prompt import Prompt
from devchat.utils import get_logger, openai_message_tokens, openai_response_tokens, update_dict

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
            combined += [
                update_dict(msg.to_dict(), "content", f"<context>\n{msg.content}\n</context>")
                for msg in self._history_messages[Message.CONTEXT]
            ]
        # History chat
        if self._history_messages[Message.CHAT]:
            combined += [msg.to_dict() for msg in self._history_messages[Message.CHAT]]
        # Request
        if self.request:
            combined += [self.request.to_dict()]
        # New context
        if self.new_context:
            combined += [
                update_dict(msg.to_dict(), "content", f"<context>\n{msg.content}\n</context>")
                for msg in self.new_context
            ]
        return combined

    def input_messages(self, messages: List[dict]):
        self._request_tokens = 0
        state = "new_instruct"
        for message_data in messages:
            self._request_tokens += openai_message_tokens(message_data, self.model)

            message = OpenAIMessage.from_dict(message_data)

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
                if message.role in ("user", "assistant", "function"):
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
            while True:
                last_message = self._history_messages[Message.CHAT].pop()
                if last_message.role in ("user", "function"):
                    self.request = last_message
                    break
                if last_message.role == "assistant":
                    self.responses.append(last_message)
                    continue
                self._history_messages[Message.CHAT].append(last_message)

    def append_new(
        self, message_type: str, content: str, available_tokens: int = sys.maxsize
    ) -> bool:
        if message_type not in (Message.INSTRUCT, Message.CONTEXT):
            raise ValueError(f"Current messages cannot be of type {message_type}.")
        # New instructions and context are of the system role
        message = OpenAIMessage(content=content, role="system")

        num_tokens = openai_message_tokens(message.to_dict(), self.model)
        if num_tokens > available_tokens:
            return False

        self._new_messages[message_type].append(message)
        self._request_tokens += num_tokens
        return True

    def set_functions(self, functions, available_tokens: int = sys.maxsize):
        num_tokens = openai_message_tokens({"functions": json.dumps(functions)}, self.model)
        if num_tokens > available_tokens:
            return False

        self._new_messages[Message.FUNCTION] = functions
        self._request_tokens += num_tokens
        return True

    def get_functions(self):
        return self._new_messages.get(Message.FUNCTION, None)

    def _prepend_history(
        self, message_type: str, message: Message, token_limit: int = sys.maxsize
    ) -> bool:
        if message_type == Message.INSTRUCT:
            raise ValueError("History messages cannot be of type INSTRUCT.")
        num_tokens = openai_message_tokens(message.to_dict(), self.model)
        if num_tokens > token_limit - self._request_tokens:
            return False
        self._history_messages[message_type].insert(0, message)
        self._request_tokens += num_tokens
        return True

    def prepend_history(self, prompt: "OpenAIPrompt", token_limit: int = sys.maxsize) -> bool:
        # Prepend the first response and the request of the prompt
        if not self._prepend_history(Message.CHAT, prompt.responses[0], token_limit):
            return False
        if not self._prepend_history(Message.CHAT, prompt.request, token_limit):
            return False

        # Append the context messages of the appended prompt
        for context_message in prompt.new_context:
            if not self._prepend_history(Message.CONTEXT, context_message, token_limit):
                return False
        return True

    def set_request(self, content: str, function_name: Optional[str] = None) -> int:
        if not content.strip():
            raise ValueError("The request cannot be empty.")
        message = OpenAIMessage(
            content=content, role=("user" if not function_name else "function"), name=function_name
        )
        self.request = message
        self._request_tokens += openai_message_tokens(message.to_dict(), self.model)

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

        self._request_tokens = response_data["usage"]["prompt_tokens"]
        self._response_tokens = response_data["usage"]["completion_tokens"]

        for choice in response_data["choices"]:
            index = choice["index"]
            if index >= len(self.responses):
                self.responses.extend([None] * (index - len(self.responses) + 1))
                self._response_reasons.extend([None] * (index - len(self._response_reasons) + 1))
            self.responses[index] = OpenAIMessage.from_dict(choice["message"])
            if choice["finish_reason"]:
                self._response_reasons[index] = choice["finish_reason"]

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

        delta_content = ""
        for choice in response_data["choices"]:
            delta = choice["delta"]
            index = choice["index"]
            finish_reason = choice["finish_reason"]

            if index >= len(self.responses):
                self.responses.extend([None] * (index - len(self.responses) + 1))
                self._response_reasons.extend([None] * (index - len(self._response_reasons) + 1))

            if not self.responses[index]:
                self.responses[index] = OpenAIMessage.from_dict(delta)
                if index == 0:
                    delta_content = self.responses[0].content if self.responses[0].content else ""
            else:
                if index == 0:
                    delta_content = self.responses[0].stream_from_dict(delta)
                else:
                    self.responses[index].stream_from_dict(delta)

                if "function_call" in delta:
                    if (
                        "name" in delta["function_call"]
                        and self.responses[index].function_call.get("name", "") == ""
                    ):
                        self.responses[index].function_call["name"] = delta["function_call"]["name"]
                    if "arguments" in delta["function_call"]:
                        self.responses[index].function_call["arguments"] = (
                            self.responses[index].function_call.get("arguments", "")
                            + delta["function_call"]["arguments"]
                        )

            if finish_reason:
                self._response_reasons[index] = finish_reason
        return delta_content

    def _count_response_tokens(self) -> int:
        return sum(openai_response_tokens(resp.to_dict(), self.model) for resp in self.responses)

    def _validate_model(self, response_data: dict):
        if not response_data["model"].startswith(self.model):
            logger.warning(
                "Model mismatch: expected '%s', got '%s'", self.model, response_data["model"]
            )

    def _timestamp_from_dict(self, response_data: dict):
        if not self._timestamp:
            self._timestamp = response_data["created"]
        elif self._timestamp != response_data["created"]:
            self._timestamp = response_data["created"]

    def _id_from_dict(self, response_data: dict):
        if self._id is None:
            self._id = response_data["id"]
        elif self._id != response_data["id"]:
            raise ValueError(f"ID mismatch: expected {self._id}, " f"got {response_data['id']}")
