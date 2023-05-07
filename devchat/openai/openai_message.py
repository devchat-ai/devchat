from dataclasses import dataclass, asdict
from typing import Optional
from devchat.message import Message


@dataclass
class OpenAIMessage(Message):
    role: str = None
    name: Optional[str] = None

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
        return state

    def stream_from_dict(self, message_data: dict) -> str:
        """Append to the message from a dictionary returned from a streaming chat API."""
        delta = message_data.get('content', '')
        self.content += delta
        return delta

    def _validate_role(self) -> bool:
        """Validate the role attribute.

        Returns:
            bool: True if the role is valid, False otherwise.
        """
        return self.role in ["system", "user", "assistant"]

    def _validate_name(self) -> bool:
        """Validate the name attribute.

        Returns:
            bool: True if the name is valid or None, False otherwise.
        """
        if self.name is None:
            return True
        if not self.name.strip():
            return False
        return len(self.name) <= 64 and self.name.replace("_", "").isalnum()
