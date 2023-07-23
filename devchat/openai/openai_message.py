import ast
import json
from dataclasses import dataclass, asdict, field, fields
from typing import Dict, Optional

from devchat.message import Message


@dataclass
class OpenAIMessage(Message):
    role: str = None
    name: Optional[str] = None
    function_call: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self._validate_role():
            raise ValueError("Invalid role. Must be one of 'system', 'user', or 'assistant'.")

        if not self._validate_name():
            raise ValueError("Invalid name. Must contain a-z, A-Z, 0-9, and underscores, "
                             "with a maximum length of 64 characters.")

    def to_dict(self) -> dict:
        state = asdict(self)
        if state['name'] is None:
            del state['name']
        if not state['function_call'] or len(state['function_call'].keys()) == 0:
            del state['function_call']
        return state

    @classmethod
    def from_dict(cls, message_data: dict) -> 'OpenAIMessage':
        keys = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in message_data.items() if k in keys}
        return cls(**kwargs)

    def function_call_to_json(self):
        '''
        convert function_call to json
        function_call is like this:
        {
            "name": function_name,
            "arguments": '{"key": """value"""}'
        }
        '''
        if not self.function_call:
            return ''
        function_call_copy = self.function_call.copy()
        if 'arguments' in function_call_copy:
            # arguments field may be not a json string
            # we can try parse it by eval
            try:
                function_call_copy['arguments'] = ast.literal_eval(function_call_copy['arguments'])
            except Exception:
                # if it is not a json string, we can do nothing
                try:
                    function_call_copy['arguments'] = json.loads(function_call_copy['arguments'])
                except Exception:
                    pass
        return '```command\n' + json.dumps(function_call_copy) + '\n```'

    def stream_from_dict(self, message_data: dict) -> str:
        """Append to the message from a dictionary returned from a streaming chat API."""
        delta = message_data.get('content', '')
        if self.content:
            self.content += delta
        else:
            self.content = delta

        return delta

    def _validate_role(self) -> bool:
        """Validate the role attribute.

        Returns:
            bool: True if the role is valid, False otherwise.
        """
        return self.role in ["system", "user", "assistant", "function"]

    def _validate_name(self) -> bool:
        """Validate the name attribute.

        Returns:
            bool: True if the name is valid or None, False otherwise.
        """
        return self._validate_string(self.name)

    def _validate_string(self, string: str) -> bool:
        """Validate a string attribute.

        Returns:
            bool: True if the string is valid or None, False otherwise.
        """
        if string is None:
            return True
        if not string.strip():
            return False
        return len(string) <= 64 and string.replace("_", "").isalnum()
