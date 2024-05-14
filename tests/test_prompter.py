import os

from devchat.engine import Namespace, RecursivePrompter


def test_prompter(tmp_path):
    namespace = Namespace(tmp_path)
    prompter = RecursivePrompter(namespace)

    # Test when there are no 'prompt.txt' files
    os.makedirs(os.path.join(tmp_path, "usr", "a", "b", "c"))
    assert prompter.run("a.b.c") == ""

    # Test when there is a 'prompt.txt' file in one ancestor
    os.makedirs(os.path.join(tmp_path, "sys", "a", "b", "c"))
    with open(os.path.join(tmp_path, "sys", "a", "prompt.txt"), "w", encoding="utf-8") as file:
        file.write("prompt a")
    assert prompter.run("a.b.c") == "prompt a\n"

    # Test when there are 'prompt.txt' files in multiple ancestors
    with open(os.path.join(tmp_path, "usr", "a", "b", "prompt.txt"), "w", encoding="utf-8") as file:
        file.write("prompt b")
    assert prompter.run("a.b.c") == "prompt a\nprompt b\n"
