class ChatMemory:
    """
    ChatMemory is the base class for all chat memory classes.
    """

    def __init__(self):
        pass

    def append(self, request, response):
        """
        Append a request and response to the memory.
        """
        # it must implemented in sub class

    def append_request(self, request):
        """
        Append a request to the memory.
        """

    def append_response(self, response):
        """
        Append a request to the memory.
        """

    def contexts(self):
        """
        Return the contexts of the memory.
        """
