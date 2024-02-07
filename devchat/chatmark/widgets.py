from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from .iobase import pipe_interaction


class Widget(ABC):
    """
    Abstract base class for widgets
    """

    def __init__(self, submit: Optional[str] = None, cancel: Optional[str] = None):
        self._rendered = False
        # Prefix for IDs/keys in the widget
        self._id_prefix = self.gen_id_prefix()
        self._submit = submit
        self._cancel = cancel

    @abstractmethod
    def _in_chatmark(self) -> str:
        """
        Generate ChatMark syntax for the widget
        """
        pass

    @abstractmethod
    def _parse_response(self, response: Dict) -> None:
        """
        Parse ChatMark response from user input
        """
        pass

    def render(self) -> None:
        """
        Render the widget to receive user input
        """
        if self._rendered:
            # already rendered once
            # not sure if the constraint is necessary
            # could be removed if re-rendering is needed
            raise RuntimeError("Widget can only be rendered once")

        self._rendered = True

        chatmark_header = "```chatmark"
        chatmark_header += f" submit={self._submit}" if self._submit else ""
        chatmark_header += f" cancel={self._cancel}" if self._cancel else ""

        lines = [
            chatmark_header,
            self._in_chatmark(),
            "```",
        ]

        chatmark = "\n".join(lines)
        response = pipe_interaction(chatmark)
        self._parse_response(response)

    @staticmethod
    def gen_id_prefix() -> str:
        return uuid4().hex

    @staticmethod
    def gen_id(id_prefix: str, index: int) -> str:
        return f"{id_prefix}_{index}"

    @staticmethod
    def parse_id(a_id: str) -> Tuple[Optional[str], Optional[int]]:
        try:
            id_prefix, index = a_id.split("_")
            return id_prefix, int(index)
        except Exception:
            return None, None


class Checkbox(Widget):
    """
    ChatMark syntax:
    ```chatmark
    Which files would you like to commit? I've suggested a few.
    > [x](file1) devchat/engine/prompter.py
    > [x](file2) devchat/prompt.py
    > [](file3) tests/test_cli_prompt.py
    ```

    Response:
    ```yaml
    file1: checked
    file3: checked
    ```
    """

    def __init__(
        self,
        options: List[str],
        check_states: Optional[List[bool]] = None,
        title: Optional[str] = None,
        submit_button_name: str = "Submit",
        cancel_button_name: str = "Cancel",
    ):
        """
        options: options to be selected
        check_states: initial check states of options, default to all False
        title: title of the widget
        """
        super().__init__(submit_button_name, cancel_button_name)

        if check_states is not None:
            assert len(options) == len(check_states)
        else:
            check_states = [False for _ in options]

        self._options = options
        self._states = check_states
        self._title = title

        self._selections: Optional[List[int]] = None

    @property
    def selections(self) -> Optional[List[int]]:
        """
        Get the indices of selected options
        """
        return self._selections

    @property
    def options(self) -> List[str]:
        """
        Get the options
        """
        return self._options

    def _in_chatmark(self) -> str:
        """
        Generate ChatMark syntax for checkbox options
        Use the index of option to generate id/key
        """
        lines = []

        if self._title:
            lines.append(self._title)

        for idx, (option, state) in enumerate(zip(self._options, self._states)):
            mark = "[x]" if state else "[]"
            key = self.gen_id(self._id_prefix, idx)
            lines.append(f"> {mark}({key}) {option}")

        text = "\n".join(lines)
        return text

    def _parse_response(self, response: Dict):
        selections = []
        for key, value in response.items():
            prefix, index = self.parse_id(key)
            # check if the prefix is the same as the widget's
            if prefix != self._id_prefix:
                continue

            if value == "checked":
                selections.append(index)

        self._selections = selections


class TextEditor(Widget):
    """
    ChatMark syntax:
    ```chatmark
    I've drafted a commit message for you as below. Feel free to modify it.

    > | (ID)
    > fix: prevent racing of requests
    >
    > Introduce a request id and a reference to latest request. Dismiss
    > incoming responses other than from latest request.
    >
    > Reviewed-by: Z
    > Refs: #123
    ```

    Response:
    ```yaml
    ID: |
        fix: prevent racing of requests

        Introduce a request ID and a reference to latest request. Dismiss
        incoming responses other than from latest request.

        Reviewed-by: Z
        Refs: #123
    ```
    """

    def __init__(
        self,
        text: str,
        title: Optional[str] = None,
        submit_button_name: str = "Submit",
        cancel_button_name: str = "Cancel",
    ):
        super().__init__(submit_button_name, cancel_button_name)

        self._title = title
        self._text = text

        self._editor_key = self.gen_id(self._id_prefix, 0)
        self._new_text: Optional[str] = None

    @property
    def new_text(self):
        return self._new_text

    def _in_chatmark(self) -> str:
        """
        Generate ChatMark syntax for text editor
        Use _editor_key as id
        """
        lines = self._text.split("\n")
        new_lines = []

        if self._title:
            new_lines.append(self._title)

        new_lines.append(f"> | ({self._editor_key})")
        new_lines.extend([f"> {line}" for line in lines])

        text = "\n".join(new_lines)
        return text

    def _parse_response(self, response: Dict):
        self._new_text = response.get(self._editor_key, None)


class Radio(Widget):
    """
    ChatMark syntax:
    ```chatmark
    How would you like to make the change?
    > - (insert) Insert the new code.
    > - (new) Put the code in a new file.
    > - (replace) Replace the current code.
    ```

    Reponse:
    ```yaml
    replace: checked
    ```
    """

    def __init__(
        self,
        options: List[str],
        default_selected: Optional[int] = None,
        title: Optional[str] = None,
        submit_button_name: str = "Submit",
        cancel_button_name: str = "Cancel",
    ) -> None:
        """
        options: options to be selected
        default_selected: index of the option to be selected by default, default to None
        title: title of the widget
        """
        if default_selected is not None:
            assert 0 <= default_selected < len(options)

        super().__init__(submit_button_name, cancel_button_name)

        self._options = options
        self._title = title

        self._selection: Optional[int] = default_selected

    @property
    def options(self) -> List[str]:
        """
        Return the options
        """
        return self._options

    @property
    def selection(self) -> Optional[int]:
        """
        Return the index of the selected option
        """
        return self._selection

    def _in_chatmark(self) -> str:
        """
        Generate ChatMark syntax for options
        Use the index of option to generate id/key
        """
        lines = []

        if self._title:
            lines.append(self._title)

        for idx, option in enumerate(self._options):
            key = self.gen_id(self._id_prefix, idx)
            if self._selection is not None and self._selection == idx:
                lines.append(f"> x ({key}) {option}")
            else:
                lines.append(f"> - ({key}) {option}")

        text = "\n".join(lines)
        return text

    def _parse_response(self, response: Dict):
        selected = None
        for key, value in response.items():
            prefix, idx = self.parse_id(key)
            # check if the prefix is the same as the widget's
            if prefix != self._id_prefix:
                continue

            if value == "checked":
                selected = idx
                break

        self._selection = selected


class Button(Widget):
    """
    ChatMark syntax:
    ```chatmark
    Would you like to pay $0.02 for this LLM query?
    > (Confirm) Yes, go ahead!
    > (Cancel) No, let's skip this.
    ```

    ```yaml
    Confirm: clicked
    ```

    # NOTE: almost the same as Radio essentially
    """

    def __init__(
        self,
        buttons: List[str],
        title: Optional[str] = None,
    ) -> None:
        """
        buttons: button names to show
        title: title of the widget
        """
        super().__init__()

        self._buttons = buttons
        self._title = title

        self._clicked: Optional[int] = None

    @property
    def clicked(self) -> Optional[int]:
        """
        Return the index of the clicked button
        """
        return self._clicked

    @property
    def buttons(self) -> List[str]:
        """
        Return the buttons
        """
        return self._buttons

    def _in_chatmark(self) -> str:
        """
        Generate ChatMark syntax for options
        Use the index of button to generate id/key
        """
        lines = []

        if self._title:
            lines.append(self._title)

        for idx, button in enumerate(self._buttons):
            key = self.gen_id(self._id_prefix, idx)
            lines.append(f"> ({key}) {button}")

        text = "\n".join(lines)
        return text

    def _parse_response(self, response: Dict[str, str]):
        clicked = None
        for key, value in response.items():
            prefix, idx = self.parse_id(key)
            # check if the prefix is the same as the widget's
            if prefix != self._id_prefix:
                continue

            if value == "clicked":
                clicked = idx
                break
        self._clicked = clicked
