import os
from typing import List

from .command_runner import CommandRunner
from .namespace import Namespace
from .recursive_prompter import RecursivePrompter
from .util import CommandUtil


def load_workflow_instruction(user_input: str):
    user_input = user_input.strip()
    if len(user_input) == 0:
        return None
    if user_input[:1] != "/":
        return None

    workflows_dir = os.path.join(os.path.expanduser("~/.chat"), "workflows")
    if not os.path.exists(workflows_dir):
        return None
    if not os.path.isdir(workflows_dir):
        return None

    namespace = Namespace(workflows_dir)
    prompter = RecursivePrompter(namespace)

    command_name = user_input.split()[0][1:]
    command_prompts = prompter.run(command_name)

    return [command_prompts]


def run_command(
    model_name: str, history_messages: List[dict], input_text: str, parent_hash: str, auto_fun: bool
):
    """
    load command config, and then run Command
    """
    # split input_text by ' ','\n','\t'
    if len(input_text.strip()) == 0:
        return None
    if input_text.strip()[:1] != "/":
        if not (auto_fun and model_name.startswith("gpt-")):
            return None

        # TODO
        # use auto select workflow to run command
        return None

    commands = input_text.split()
    command = commands[0][1:]

    command_obj = CommandUtil.load_command(command)
    if not command_obj or not command_obj.steps:
        return None

    runner = CommandRunner(model_name)
    return runner.run_command(
        command_name=command,
        command=command_obj,
        history_messages=history_messages,
        input_text=input_text,
        parent_hash=parent_hash,
    )
