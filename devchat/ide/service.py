import os
from functools import wraps
from typing import List

import requests

from .types import Location, SymbolNode

BASE_SERVER_URL = os.environ.get("DEVCHAT_IDE_SERVICE_URL", "http://localhost:3000")


def rpc_method(f):
    """
    Decorator for Service methods
    """

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if os.environ.get("DEVCHAT_IDE_SERVICE_URL", "") == "":
            # maybe in a test, user don't want to mock services functions
            return

        try:
            function_name = f.__name__
            url = f"{BASE_SERVER_URL}/{function_name}"

            data = dict(zip(f.__code__.co_varnames[1:], args))  # Exclude "self"
            data.update(kwargs)
            headers = {"Content-Type": "application/json"}

            response = requests.post(url, json=data, headers=headers)

            if response.status_code != 200:
                raise Exception(f"Server error: {response.status_code}")

            response_data = response.json()
            if "error" in response_data:
                raise Exception(f"Server returned an error: {response_data['error']}")

            # Store the result in the _result attribute of the instance
            self._result = response_data.get("result", None)
            return f(self, *args, **kwargs)

        except ConnectionError as err:
            # TODO
            raise err

    return wrapper


class IDEService:
    """
    Client for IDE service

    Usage:
    client = IDEService()
    res = client.ide_language()
    res = client.ide_logging("info", "some message")
    """

    def __init__(self):
        self._result = None

    @rpc_method
    def get_lsp_brige_port(self) -> str:
        return self._result

    @rpc_method
    def install_python_env(self, command_name: str, requirements_file: str) -> str:
        return self._result

    @rpc_method
    def update_slash_commands(self) -> bool:
        return self._result

    @rpc_method
    def ide_language(self) -> str:
        return self._result

    @rpc_method
    def ide_logging(self, level: str, message: str) -> bool:
        """
        level: "info" | "warn" | "error" | "debug"
        """
        return self._result

    @rpc_method
    def get_document_symbols(self, abspath: str) -> List[SymbolNode]:
        return [SymbolNode.parse_obj(node) for node in self._result]

    @rpc_method
    def find_type_def_locations(self, abspath: str, line: int, character: int) -> List[Location]:
        return [Location.parse_obj(loc) for loc in self._result]
