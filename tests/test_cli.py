"""
This module contains tests for the devchat CLI.
"""

import io
from contextlib import redirect_stdout
from devchat._cli import main

def test_main():
    """
    Test the main function of the CLI. Ensures it prints "Hello, World!" as expected.
    """
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        main()
    output = buffer.getvalue().strip()
    assert output == "Hello World"
