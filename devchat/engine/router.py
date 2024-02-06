from typing import List
from .command_runner import CommandRunner
from .util import CommandUtil


def run_command(
        model_name: str,
        history_messages: List[dict],
        input_text: str,
        parent_hash: str,
        auto_fun: bool):
    """
    load command config, and then run Command
    """
    # split input_text by ' ','\n','\t'
    if len(input_text.strip()) == 0:
        return None
    if input_text.strip()[:1] != '/':
        if not (auto_fun and model_name.startswith('gpt-')):
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
        parent_hash=parent_hash
    )
