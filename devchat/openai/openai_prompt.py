import json
import hashlib
from devchat.prompt import Prompt
from devchat.message import MessageType
from .openai_message import OpenAIMessage


class OpenAIPrompt(Prompt):
    """
    A class to represent a prompt and its corresponding responses from OpenAI APIs.
    """

    def __init__(self, model: str, user_name: str, user_email: str):
        super().__init__(user_name, user_email)
        self._model: str = model
        self._id: str = None

    @property
    def model(self) -> str:
        return self._model

    @property
    def id(self) -> str:
        return self._id

    def append_message(self, message: OpenAIMessage):
        """
        Append a message to the prompt.

        Args:
            message (Message): The message to append.
        """
        self._messages.append(message)

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

        self._responses = {
            choice['index']: OpenAIMessage.from_dict(MessageType.RECORD, choice['message'])
            for choice in response_data['choices']
        }

        self._hashes = {
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
        self._timestamp_from_dict(response_data)
        self._id_from_dict(response_data)

        delta_content = ''
        for choice in response_data['choices']:
            delta = choice['delta']
            index = choice['index']

            if index not in self.responses:
                self.responses[index] = OpenAIMessage.from_dict(MessageType.RECORD, delta)
                if index == 0:
                    delta_content = self.formatted_header()
                    delta_content += self.responses[0].content
            else:
                if index == 0:
                    delta_content = self.responses[0].append_from_dict(delta)
                else:
                    self.responses[index].append_from_dict(delta)

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
