from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
from typing import Dict


@dataclass
class Message(ABC):
    """
    The basic unit of information in a prompt.
    """
    content: str = ""
    function_call: Dict = field(default_factory=dict)

    INSTRUCT = "instruct"
    CONTEXT = "context"
    FUNCTION = "function"
    CHAT = "chat"

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert the message to a dictionary.
        """
        
    def function_to_block(self) -> str:
        """
        Convert funtion call to a block of code.
        """
        if self.function_call:
            arguments_content = self.function_call["arguments"]

            try:
                arguments_obj = eval(arguments_content)
            except Exception:
                try:
                    arguments_obj = json.loads(arguments_content)
                except Exception:
                    arguments_obj = arguments_content
                    
            function_call_new = {"name": self.function_call["name"], "arguments": arguments_obj}
            return f"\n```command\n{json.dumps(function_call_new, indent=4)}\n```"
        else:
            return ""

    @abstractmethod
    def stream_from_dict(self, message_data: dict) -> str:
        """
        Append to the message from a dictionary returned from a streaming chat API.
        """
