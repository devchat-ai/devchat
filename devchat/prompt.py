import json
import hashlib
from typing import Dict
from devchat.message import Message
from devchat.utils import unix_to_local_datetime


class Prompt:
    """
    A class to represent a prompt and its corresponding response from the chat API.

    Attributes:
        model (str): The model used for the chat API request, e.g., "gpt-3.5-turbo".
        user_name (str): The name of the user.
        user_email (str): The email address of the user.
        response_meta (dict): A dictionary containing the 'id' and 'object' fields of the response.
        response_time (int): The timestamp when the response was created.
        request_tokens (int): The number of tokens used in the request.
        response_tokens (int): The number of tokens used in the response.
        responses (Dict[int, Message]): The responses indexed by an integer.
        prompt_hashes (Dict[int, str]): The hashes of the prompts indexed by an integer.
    """

    def __init__(self, model: str, user_name: str, user_email: str):
        self.model: str = model
        self.user_name: str = user_name
        self.user_email: str = user_email
        self.response_meta: dict = None
        self.response_time: int = None
        self.request_tokens: int = None
        self.response_tokens: int = None
        self.responses: Dict[int, Message] = {}

    def set_response(self, response_str: str):
        """
        Parse the API response string and set the Prompt object's attributes.

        Args:
            response_str (str): The JSON-formatted response string from the chat API.
        """
        response_data = json.loads(response_str)
        self._validate_model(response_data)

        self.response_meta = {
            'id': response_data['id'],
            'object': response_data['object']
        }
        self.response_time = response_data['created']
        self.request_tokens = response_data['usage']['prompt_tokens']
        self.response_tokens = response_data['usage']['completion_tokens']

        self.responses = {
            choice['index']: Message.from_dict(choice['message'])
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
                    self.responses[index] = Message(role)
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

    def _validate_model(self, response_data: dict):
        if not response_data['model'].startswith(self.model):
            raise ValueError(f"Model mismatch: expected '{self.model}', "
                             f"got '{response_data['model']}'")
