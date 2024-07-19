import json
import sys
import time
from typing import Iterator, List, Optional

from devchat.chat import Chat
from devchat.message import Message
from devchat.openai.openai_prompt import OpenAIPrompt
from devchat.store import Store
from devchat.utils import get_logger

logger = get_logger(__name__)


class Assistant:
    def __init__(self, chat: Chat, store: Store, max_prompt_tokens: int, need_store: bool):
        """
        Initializes an Assistant object.

        Args:
            chat (Chat): A Chat object used to communicate with chat APIs.
        """
        self._chat = chat
        self._store = store
        self._prompt = None
        self.token_limit = max_prompt_tokens
        self._need_store = need_store

    @property
    def prompt(self) -> OpenAIPrompt:
        return self._prompt

    @property
    def available_tokens(self) -> int:
        return self.token_limit - self._prompt.request_tokens

    def _check_limit(self):
        if self._prompt.request_tokens > self.token_limit:
            raise ValueError(
                f"Prompt tokens {self._prompt.request_tokens} " f"beyond limit {self.token_limit}."
            )

    def make_prompt(
        self,
        request: str,
        instruct_contents: Optional[List[str]],
        context_contents: Optional[List[str]],
        functions: Optional[List[dict]],
        parent: Optional[str] = None,
        references: Optional[List[str]] = None,
        function_name: Optional[str] = None,
    ):
        """
        Make a prompt for the chat API.

        Args:
            request (str): The user request.
            instruct_contents (Optional[List[str]]): A list of instructions to the prompt.
            context_contents (Optional[List[str]]): A list of context messages to the prompt.
            parent (Optional[str]): The parent prompt hash. None means a new topic.
            references (Optional[List[str]]): The reference prompt hashes.
        """
        self._prompt = self._chat.init_prompt(request, function_name=function_name)
        self._check_limit()
        # Add instructions to the prompt
        if instruct_contents:
            combined_instruct = "".join(instruct_contents)
            self._prompt.append_new(Message.INSTRUCT, combined_instruct)
            self._check_limit()
        # Add context to the prompt
        if context_contents:
            for context_content in context_contents:
                self._prompt.append_new(Message.CONTEXT, context_content)
                self._check_limit()
        # Add functions to the prompt
        if functions:
            self._prompt.set_functions(functions)
            self._check_limit()

        # Add history to the prompt
        if references:
            for reference_hash in references:
                prompt = self._store.get_prompt(reference_hash)
                if not prompt:
                    logger.error(
                        "Reference %s not retrievable while making prompt.", reference_hash
                    )
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
            created_time = int(time.time())
            config_params = self._chat.config.dict(exclude_unset=True)
            stream_responses = self._chat.stream_response(self._prompt)
            if not stream_responses:
                raise RuntimeError("No response returned from the chat API")
            for chunk in stream_responses:
                try:
                    if hasattr(chunk, "dict"):
                        chunk = chunk.dict()
                    if len(chunk["choices"]) > 0:
                        if (
                            "function_call" in chunk["choices"][0]["delta"]
                            and not chunk["choices"][0]["delta"]["function_call"]
                        ):
                            del chunk["choices"][0]["delta"]["function_call"]
                            if not chunk["choices"][0]["delta"]["content"]:
                                chunk["choices"][0]["delta"]["content"] = ""
                        if "id" not in chunk or "index" not in chunk["choices"][0]:
                            chunk["id"] = "chatcmpl-7vdfQI02x-" + str(created_time)
                            chunk["object"] = "chat.completion.chunk"
                            chunk["created"] = created_time
                            chunk["model"] = config_params["model"]
                            chunk["choices"][0]["index"] = 0
                            chunk["choices"][0]["finish_reason"] = "stop"
                        if "role" not in chunk["choices"][0]["delta"]:
                            chunk["choices"][0]["delta"]["role"] = "assistant"

                        delta = self._prompt.append_response(json.dumps(chunk))
                        yield delta
                except Exception as err:
                    print("receive:", chunk, file=sys.stderr, end="\n\n")
                    logger.error("Error while iterating response: %s, %s", err, str(chunk))
                    raise RuntimeError(f"Error while iterating response, {err}, {str(chunk)}")
            if not self._prompt.responses:
                raise RuntimeError("No responses returned from the chat API")
            if self._need_store:
                self._store.store_prompt(self._prompt)
                yield self._prompt.formatted_footer(0) + "\n"
            for index in range(1, len(self._prompt.responses)):
                yield self._prompt.formatted_full_response(index) + "\n"
        else:
            response_str = self._chat.complete_response(self._prompt)
            self._prompt.set_response(response_str)
            if not self._prompt.responses:
                raise RuntimeError("No responses returned from the chat API")
            if self._need_store:
                self._store.store_prompt(self._prompt)
            for index in range(len(self._prompt.responses)):
                yield self._prompt.formatted_full_response(index) + "\n"
