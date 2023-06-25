from typing import Optional, List, Iterator
from devchat.message import Message
from devchat.chat import Chat
from devchat.store import Store
from devchat.utils import get_logger


logger = get_logger(__name__)


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
        self.token_limit = 3000

    @property
    def available_tokens(self) -> int:
        return self.token_limit - self._prompt.request_tokens

    def _check_limit(self):
        if self._prompt.request_tokens > self.token_limit:
            raise ValueError(f"Prompt tokens {self._prompt.request_tokens} "
                             f"beyond limit {self.token_limit}.")

    def make_prompt(self, request: str,
                    instruct_contents: Optional[List[str]], context_contents: Optional[List[str]],
                    parent: Optional[str] = None, references: Optional[List[str]] = None):
        """
        Make a prompt for the chat API.

        Args:
            request (str): The user request.
            instruct_contents (Optional[List[str]]): A list of instructions to the prompt.
            context_contents (Optional[List[str]]): A list of context messages to the prompt.
            parent (Optional[str]): The parent prompt hash. None means a new topic.
            references (Optional[List[str]]): The reference prompt hashes.
        """
        self._prompt = self._chat.init_prompt(request)
        self._check_limit()
        # Add instructions to the prompt
        if instruct_contents:
            combined_instruct = ''.join(instruct_contents)
            self._prompt.append_new(Message.INSTRUCT, combined_instruct)
            self._check_limit()
        # Add context to the prompt
        if context_contents:
            for context_content in context_contents:
                self._prompt.append_new(Message.CONTEXT, context_content)
                self._check_limit()

        # Add history to the prompt
        for reference_hash in references:
            prompt = self._store.get_prompt(reference_hash)
            if not prompt:
                logger.error("Reference %s not retrievable while making prompt.", reference_hash)
                continue
            self._prompt.references.append(reference_hash)
            self._prompt.prepend_history(prompt, self.token_limit)
        if parent:
            self._prompt.parent = parent
            parent_hash = parent
            while parent_hash:
                parent_prompt = self._store.get_prompt(parent_hash)
                if not parent_prompt:
                    logger.error("Parent %s not retrievable while making prompt.", parent_hash)
                    break
                if not self._prompt.prepend_history(parent_prompt, self.token_limit):
                    break
                parent_hash = parent_prompt.parent

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
            for index in range(len(self._prompt.response)):
                yield self._prompt.formatted_response(index) + '\n'
