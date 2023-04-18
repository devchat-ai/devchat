import io
from contextlib import redirect_stdout
from devchat._cli import main

def test_main():
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        main()
    output = buffer.getvalue().strip()
    assert output == "Hello World"
