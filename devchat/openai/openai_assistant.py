import os
import sys
from typing import Optional, List, Iterator
from devchat.utils import get_git_user_info, is_valid_hash
from devchat.message import MessageType
from .openai_prompt import OpenAIPrompt
from .openai_chat import OpenAIChat


class OpenAIAssistant:
    def __init__(self, chat: OpenAIChat):
        """
        Initializes an OpenAIAssistant object.

        Args:
            chat (OpenAIChat): An OpenAIChat object used to communicate with OpenAI APIs.
        """
        self._chat = chat
        user, email = get_git_user_info()
        self._openai_prompt = OpenAIPrompt(self._chat.config.model, user, email)

    def make_prompt(self, content: str,
                    instruct_contents: Optional[List[str]], context_contents: Optional[List[str]],
                    parent: Optional[str] = None, reference: Optional[List[str]] = None):
        """
        Make a prompt for the chat API.

        Args:
            content (str): The user request.
            instruct_contents (Optional[List[str]]): A list of instructions to the prompt.
            context_contents (Optional[List[str]]): A list of context messages to the prompt.
            parent (Optional[str]): The ID of the parent prompt.
            references (Optional[List[str]]): A list of IDs of reference prompts.
        """
        # Validate hashes
        self._validate_hashes(parent, reference)

        # Add instructions to the prompt
        if instruct_contents:
            combined_instruct = ''.join(instruct_contents)
            self._openai_prompt.append_message(MessageType.INSTRUCT, combined_instruct)
        # Set user request
        self._openai_prompt.set_request(content)
        # Add context to the prompt
        if context_contents:
            for context_content in context_contents:
                self._openai_prompt.append_message(MessageType.CONTEXT, context_content)
        self._chat.request(self._openai_prompt)

    def iterate_responses(self) -> Iterator[str]:
        """Get an iterator of response strings from the chat API.

        Returns:
            Iterator[str]: An iterator over response strings from the chat API.
        """
        if self._chat.config.stream:
            response_iterator = self._chat.stream_response()
            for chunk in response_iterator:
                yield self._openai_prompt.append_response(str(chunk))
            yield f'\n\nprompt {self._openai_prompt.hash(0)}\n'
            for index in range(1, len(self._openai_prompt.responses)):
                yield self._openai_prompt.formatted_response(index) + '\n'
        else:
            response_str = str(self._chat.complete_response())
            self._openai_prompt.set_response(response_str)
            for index in self._openai_prompt.responses.keys():
                yield self._openai_prompt.formatted_response(index) + '\n'

    @classmethod
    def _validate_hashes(cls, parent, reference):
        if parent is not None:
            for parent_hash in parent.split(','):
                if not is_valid_hash(parent_hash):
                    sys.exit(os.EX_DATAERR)

        if reference is not None:
            for reference_hash in reference.split(','):
                if not is_valid_hash(reference_hash):
                    sys.exit(os.EX_DATAERR)
