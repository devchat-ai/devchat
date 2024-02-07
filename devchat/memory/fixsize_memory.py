from .base import ChatMemory


class FixSizeChatMemory(ChatMemory):
    """
    FixSizeChatMemory is a memory class that stores up
    to a fixed number of requests and responses.
    """

    def __init__(self, max_size: int = 5, messages=[], system_prompt=None):
        """
        init the memory
        """
        super().__init__()
        self._max_size = max_size
        # store last max_size messages
        self._messages = messages[-max_size * 2 :]
        self._system_prompt = system_prompt

    def append(self, request, response):
        """
        Append a request and response to the memory.
        """
        self._messages.append(request)
        self._messages.append(response)
        if len(self._messages) > self._max_size * 2:
            self._messages = self._messages[-self._max_size * 2 :]

    def append_request(self, request):
        """
        Append a request to the memory.
        """
        self._messages.append(request)

    def append_response(self, response):
        """
        Append a response to the memory.
        """
        self._messages.append(response)
        if len(self._messages) > self._max_size * 2:
            self._messages = self._messages[-self._max_size * 2 :]

    def contexts(self):
        """
        Return the contexts of the memory.
        """
        messages = self._messages.copy()
        # insert system prompt at the beginning
        if self._system_prompt:
            messages = [{"role": "system", "content": self._system_prompt}] + messages
        return messages
