import json
from devchat.message import Message

class Prompt:
    """
    A class to represent a prompt and its corresponding response from the chat API.

    Attributes:
        model (str): The model used for the chat API request, e.g., "gpt-3.5-turbo".
        response_meta (dict): A dictionary containing the 'id' and 'object' fields of the response.
        response_time (int): The timestamp when the response was created.
        request_tokens (int): The number of tokens used in the request.
        response_tokens (int): The number of tokens used in the response.
        messages (List[Message]): A list of Message instances containing the conversation messages.
    """

    def __init__(self, model: str):
        self.model = model
        self.response_meta = None
        self.response_time = None
        self.request_tokens = None
        self.response_tokens = None
        self.messages = None

    def set_response(self, response_str: str):
        """
        Parse the API response string and set the Prompt object's attributes.

        Args:
            response_str (str): The JSON-formatted response string from the chat API.
        """
        response_data = json.loads(response_str)

        if not response_data['model'].startswith(self.model):
            raise ValueError(f"Model mismatch: expected '{self.model}', "
                             f"got '{response_data['model']}'")

        self.response_meta = {
            'id': response_data['id'],
            'object': response_data['object']
        }
        self.response_time = response_data['created']
        self.request_tokens = response_data['usage']['prompt_tokens']
        self.response_tokens = response_data['usage']['completion_tokens']

        self.messages = [
            Message.from_dict(choice['message'])
            for choice in response_data['choices']
        ]
