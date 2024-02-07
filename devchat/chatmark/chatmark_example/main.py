import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "libs"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "libs"))

from chatmark import Button, Checkbox, Form, Radio, Step, TextEditor  # noqa: E402


def main():
    print("\n\n---\n\n")

    # Step
    print("\n\n# Step Example\n\n")
    with Step("Something is running..."):
        print("Will sleep for 5 seconds...", flush=True)
        time.sleep(5)
        print("Done", flush=True)

    print("\n\n# Step Example with exception\n\n")
    try:
        with Step("Something is running (will raise exception)..."):
            print("Will sleep for 5 seconds...", flush=True)
            time.sleep(5)
            raise Exception("oops!")

    except Exception:
        pass

    # Button
    print("\n\n# Button Example\n\n")
    button = Button(
        [
            "Yes",
            "Or",
            "No",
        ],
    )
    button.render()

    idx = button.clicked
    print("\n\nButton result\n\n")
    print(f"\n\n{idx}: {button.buttons[idx]}\n\n")

    print("\n\n---\n\n")

    # Checkbox
    print("\n\n# Checkbox Example\n\n")
    checkbox = Checkbox(
        [
            "A",
            "B",
            "C",
            "D",
        ],
        [True, False, False, True],
    )
    checkbox.render()

    print(f"\n\ncheckbox.selections: {checkbox.selections}\n\n")
    for idx in checkbox.selections:
        print(f"\n\n{idx}: {checkbox.options[idx]}\n\n")

    print("\n\n---\n\n")

    # TextEditor
    print("\n\n# TextEditor Example\n\n")
    text_editor = TextEditor(
        "hello world\nnice to meet you",
    )

    text_editor.render()

    print(f"\n\ntext_editor.new_text:\n\n{text_editor.new_text}\n\n")

    print("\n\n---\n\n")

    # Radio
    print("\n\n# Radio Example\n\n")
    radio = Radio(
        [
            "Sun",
            "Moon",
            "Star",
        ],
    )
    radio.render()

    print(f"\n\nradio.selection: {radio.selection}\n\n")
    if radio.selection is not None:
        print(f"\n\nradio.options[radio.selection]: {radio.options[radio.selection]}\n\n")

    print("\n\n---\n\n")

    # Form
    print("\n\n# Form Example\n\n")
    checkbox_1 = Checkbox(
        [
            "Sprint",
            "Summer",
            "Autumn",
            "Winter",
        ]
    )
    checkbox_2 = Checkbox(
        [
            "金",
            "木",
            "水",
            "火",
            "土",
        ],
    )
    radio_1 = Radio(
        [
            "Up",
            "Down",
        ],
    )
    radio_2 = Radio(
        [
            "Left",
            "Center",
            "Right",
        ],
    )
    text_editor_1 = TextEditor(
        "hello world\nnice to meet you",
    )
    text_editor_2 = TextEditor(
        "hihihihihi",
    )

    form = Form(
        [
            "Some string in a form",
            checkbox_1,
            "Another string in a form",
            radio_1,
            "the third string in a form",
            checkbox_2,
            "the fourth string in a form",
            radio_2,
            "the fifth string in a form",
            text_editor_1,
            "the last string in a form",
            text_editor_2,
        ],
    )

    form.render()

    print(f"\n\ncheckbox_1.selections: {checkbox_1.selections}\n\n")
    print(f"\n\ncheckbox_2.selections: {checkbox_2.selections}\n\n")
    print(f"\n\nradio_1.selection: {radio_1.selection}\n\n")
    print(f"\n\nradio_2.selection: {radio_2.selection}\n\n")
    print(f"\n\ntext_editor_1.new_text:\n\n{text_editor_1.new_text}\n\n")
    print(f"\n\ntext_editor_2.new_text:\n\n{text_editor_2.new_text}\n\n")


if __name__ == "__main__":
    main()
