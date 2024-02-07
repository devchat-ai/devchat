from contextlib import AbstractContextManager


class Step(AbstractContextManager):
    """
    Show a running step in the TUI.

    ChatMark syntax:

    ```Step
    # Something is running...
    some details...
    ```

    Usage:
    with Step("Something is running..."):
        print("some details...")
    """

    def __init__(self, title: str):
        self.title = title

    def __enter__(self):
        print(f"\n```Step\n# {self.title}", flush=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # close the step
        print("\n```", flush=True)
