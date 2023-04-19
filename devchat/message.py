from typing import Optional

class Message:
    """A class to represent a message in a conversation with chat API.

    Attributes:
        role (str): The role of the author of the message. One of 'system', 'user', or 'assistant'.
        content (str): The contents of the message.
        name (str, optional): The name of the author of the message. May contain a-z, A-Z, 0-9, and
                              underscores, with a maximum length of 64 characters.
    """

    def __init__(self, role: str, content: str, name: Optional[str] = None):
        self.role = role
        self.content = content
        self.name = name

        if not self._validate_role():
            raise ValueError("Invalid role. Must be one of 'system', 'user', or 'assistant'.")

        if not self._validate_content():
            raise ValueError("Content must not be empty or contain only whitespaces.")

        if not self._validate_name():
            raise ValueError("Invalid name. Must contain a-z, A-Z, 0-9, and underscores, "
                             "with a maximum length of 64 characters.")

    def _validate_role(self) -> bool:
        """Validate the role attribute.

        Returns:
            bool: True if the role is valid, False otherwise.
        """
        return self.role in ["system", "user", "assistant"]

    def _validate_content(self) -> bool:
        """Validate the content attribute.

        Returns:
            bool: True if the content is valid, False otherwise.
        """
        return bool(self.content and self.content.strip())

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

    def to_dict(self) -> dict:
        """Convert the Message object to a dictionary.

        Returns:
            dict: A dictionary representation of the Message object.
        """
        message_dict = {
            "role": self.role,
            "content": self.content,
        }
        if self.name is not None:
            message_dict["name"] = self.name
        return message_dict
