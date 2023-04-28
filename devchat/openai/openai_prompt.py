import json
import hashlib
from typing import Dict, List
from devchat.prompt import Prompt
from devchat.openai import OpenAIMessage
from devchat.message import Message, MessageType


class OpenAIPrompt(Prompt):
    """
    A class to represent a prompt and its corresponding responses from OpenAI APIs.
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

    def append_message(self, type: MessageType, content: str):
        """
        Append a message to the prompt.

        Args:
            message (Message): The message to append.
        """
        self.messages.append(OpenAIMessage(type, content))

    def set_response(self, response_str: str):
        """
        Parse the API response string and set the Prompt object's attributes.

        Args:
            response_str (str): The JSON-formatted response string from the chat API.
        """
        response_data = json.loads(response_str)
        self._validate_model(response_data)

        self.response_time = response_data['created']
        self.request_tokens = response_data['usage']['prompt_tokens']
        self.response_tokens = response_data['usage']['completion_tokens']

        self.responses = {
            choice['index']: OpenAIMessage.from_dict(MessageType.CONTEXT, choice['message'])
            for choice in response_data['choices']
        }

        self.prompt_hashes = {
            choice['index']: hashlib.sha1(choice['message']['content'].encode()).hexdigest()
            for choice in response_data['choices']
        }

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

        self.response_meta = {
            'id': response_data['id'],
            'object': response_data['object']
        }
        self.response_time = response_data['created']

        delta_content = ""
        for choice in response_data['choices']:
            delta = choice.get('delta')
            index = choice.get('index')

            if delta is None:
                raise ValueError("The 'delta' field is missing in the response.")

            if not delta:
                # An empty delta indicates the end of the message.
                if index == 0:
                    delta_content = None
                continue

            role = delta.get('role')
            content = delta.get('content')

            if role is not None:
                if index not in self.responses:
                    self.responses[index] = OpenAIMessage(MessageType.CONTEXT, role)
                    delta_content = self.formatted_header()

            if content is not None:
                if index in self.responses:
                    message = self.responses[index]
                    if message.content is None:
                        message.content = content
                    else:
                        message.content += content
                else:
                    raise ValueError(f"Role information for index {index} is missing.")

            if index == 0 and content is not None:
                delta_content += content

        return delta_content

    def _validate_model(self, response_data: dict):
        if not response_data['model'].startswith(self.model):
            raise ValueError(f"Model mismatch: expected '{self.model}', "
                             f"got '{response_data['model']}'")
