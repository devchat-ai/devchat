from typing import Optional, List, Iterator
from devchat.utils import parse_hashes
from devchat.message import MessageType
from devchat.chat import Chat


class Assistant:
    def __init__(self, chat: Chat):
        """
        Initializes an Assistant object.

        Args:
            chat (Chat): A Chat object used to communicate with chat APIs.
        """
        self._chat = chat
        self._prompt = None

    def make_prompt(self, request: str,
                    instruct_contents: Optional[List[str]], context_contents: Optional[List[str]],
                    parent: Optional[str] = None, reference: Optional[List[str]] = None):
        """
        Make a prompt for the chat API.

        Args:
            request (str): The user request.
            instruct_contents (Optional[List[str]]): A list of instructions to the prompt.
            context_contents (Optional[List[str]]): A list of context messages to the prompt.
            parent (Optional[str]): The ID of the parent prompt.
            references (Optional[List[str]]): A list of IDs of reference prompts.
        """
        self._prompt = self._chat.init_prompt(request)
        self._prompt.parents = parse_hashes(parent)
        self._prompt.references = parse_hashes(reference)

        # Add instructions to the prompt
        if instruct_contents:
            combined_instruct = ''.join(instruct_contents)
            self._prompt.append_message(MessageType.INSTRUCT, combined_instruct)
        # Set user request
        self._prompt.set_request(request)
        # Add context to the prompt
        if context_contents:
            for context_content in context_contents:
                self._prompt.append_message(MessageType.CONTEXT, context_content)

    def iterate_responses(self) -> Iterator[str]:
        """Get an iterator of response strings from the chat API.

        Returns:
            Iterator[str]: An iterator over response strings from the chat API.
        """
        if self._chat.config.stream:
            response_iterator = self._chat.stream_response(self._prompt)
            for chunk in response_iterator:
                yield self._prompt.append_response(str(chunk))
            self._prompt.set_hash()
            yield f'\n\nprompt {self._prompt.hash}\n'
            for index in range(1, len(self._prompt.responses)):
                yield self._prompt.formatted_response(index) + '\n'
        else:
            response_str = str(self._chat.complete_response(self._prompt))
            self._prompt.set_response(response_str)
            for index in self._prompt.responses.keys():
                yield self._prompt.formatted_response(index) + '\n'
