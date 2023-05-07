from typing import Optional, List, Iterator
from devchat.utils import validate_hashes
from devchat.message import MessageType
from devchat.chat import Chat
from devchat.prompt import Prompt
from devchat.store import Store


class Assistant:
    def __init__(self, chat: Chat, store: Store):
        """
        Initializes an Assistant object.

        Args:
            chat (Chat): A Chat object used to communicate with chat APIs.
        """
        self._chat = chat
        self._store = store
        self._prompt = None
        self.token_limit = 10
        self._message_count = 0

    def _check_limit(self) -> bool:
        return self._message_count < self.token_limit

    def make_prompt(self, request: str,
                    instruct_contents: Optional[List[str]], context_contents: Optional[List[str]],
                    parents: Optional[List[str]] = None, references: Optional[List[str]] = None):
        """
        Make a prompt for the chat API.

        Args:
            request (str): The user request.
            instruct_contents (Optional[List[str]]): A list of instructions to the prompt.
            context_contents (Optional[List[str]]): A list of context messages to the prompt.
            parents (Optional[List[str]]): The parent prompt hashes.
            references (Optional[List[str]]): The reference prompt hashes.
        """
        self._prompt = self._chat.init_prompt(request)

        self._prompt.parents = validate_hashes(parents)
        self._prompt.references = validate_hashes(references)
        for parent_hash in self._prompt.parents:
            self._append_prompt(self._store.get_prompt(parent_hash))
        for reference_hash in self._prompt.references:
            self._append_prompt(self._store.get_prompt(reference_hash))

        # Add instructions to the prompt
        if instruct_contents:
            combined_instruct = ''.join(instruct_contents)
            self._prompt.append_new(MessageType.INSTRUCT, combined_instruct)
        # Set user request
        self._prompt.set_request(request)
        # Add context to the prompt
        if context_contents:
            for context_content in context_contents:
                self._prompt.append_new(MessageType.CONTEXT, context_content)

    def iterate_response(self) -> Iterator[str]:
        """Get an iterator of response strings from the chat API.

        Returns:
            Iterator[str]: An iterator over response strings from the chat API.
        """
        if self._chat.config.stream:
            response_iterator = self._chat.stream_response(self._prompt)
            for chunk in response_iterator:
                yield self._prompt.append_response(str(chunk))
            self._store.store_prompt(self._prompt)
            yield f'\n\nprompt {self._prompt.hash}\n'
            for index in range(1, len(self._prompt.response)):
                yield self._prompt.formatted_response(index) + '\n'
        else:
            response_str = str(self._chat.complete_response(self._prompt))
            self._prompt.set_response(response_str)
            self._store.store_prompt(self._prompt)
            for index in self._prompt.response.keys():
                yield self._prompt.formatted_response(index) + '\n'

    def _append_prompt(self, prompt: Prompt):
        # Append the first response and the request of the appended prompt
        if self._check_limit():
            self._prompt.append_history(MessageType.CHAT, prompt.response[0])
            self._message_count += 1

        if self._check_limit():
            self._prompt.append_history(MessageType.CHAT, prompt.request)
            self._message_count += 1

        # Append the context messages of the appended prompt
        for context_message in prompt.new_context:
            if self._check_limit():
                self._prompt.append_history(MessageType.CONTEXT, context_message)
                self._message_count += 1
            else:
                break
