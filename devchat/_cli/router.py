import json
import sys
from typing import List, Optional
import rich_click as click
from devchat.engine import run_command, load_workflow_instruction
from devchat.assistant import Assistant
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig
from devchat.store import Store
from devchat.utils import parse_files
from devchat._cli.utils import handle_errors, init_dir, get_model_config
from devchat._cli.errors import MissContentInPromptException


def _get_model_and_config(
        model: Optional[str],
        config_str: Optional[str]):
    _1, user_chat_dir = init_dir()
    model, config = get_model_config(user_chat_dir, model)

    parameters_data = config.dict(exclude_unset=True)
    if config_str:
        config_data = json.loads(config_str)
        parameters_data.update(config_data)
    return model, parameters_data

def _load_tool_functions(functions: Optional[str]):
    try:
        if functions:
            with open(functions, 'r', encoding="utf-8") as f_file:
                return json.load(f_file)
        return None
    except Exception:
        return None

def _load_instruction_contents(content: str, instruct: Optional[List[str]]):
    instruct_contents = parse_files(instruct)
    command_instructions = load_workflow_instruction(content)
    if command_instructions is not None:
        instruct_contents.extend(command_instructions)

    return instruct_contents


def before_prompt(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None,
           functions: Optional[str] = None, function_name: Optional[str] = None,
           not_store: Optional[bool] = False):
    repo_chat_dir, _1 = init_dir()

    if content is None:
        content = click.get_text_stream('stdin').read()

    if content == '':
        raise MissContentInPromptException()

    instruct_contents = _load_instruction_contents(content, instruct)
    context_contents = parse_files(context)
    tool_functions = _load_tool_functions(functions)

    model, parameters_data = _get_model_and_config(model, config_str)
    max_input_tokens = parameters_data.get("max_input_tokens", 4000)

    openai_config = OpenAIChatConfig(model=model, **parameters_data)
    chat = OpenAIChat(openai_config)
    chat_store = Store(repo_chat_dir, chat)

    assistant = Assistant(chat, chat_store, max_input_tokens, not not_store)
    assistant.make_prompt(
        request = content,
        instruct_contents = instruct_contents,
        context_contents = context_contents,
        functions = tool_functions,
        parent=parent,
        references=reference,
        function_name=function_name
    )

    return model, assistant, content

def llm_prompt(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None,
           functions: Optional[str] = None, function_name: Optional[str] = None,
           not_store: Optional[bool] = False):
    with handle_errors():
        _1, assistant, _3, = before_prompt(
            content, parent, reference, instruct, context,
            model, config_str, functions, function_name, not_store
		)

        click.echo(assistant.prompt.formatted_header())
        for response in assistant.iterate_response():
            click.echo(response, nl=False)


def llm_commmand(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None):
    with handle_errors():
        model, assistant, content = before_prompt(
            content, parent, reference, instruct, context, model, config_str, None, None, True
		)

        click.echo(assistant.prompt.formatted_header())
        command_result = run_command(
            model_name = model,
            history_messages = assistant.prompt.messages,
            input_text = content,
            parent_hash = parent,
            auto_fun = False)
        if command_result is not None:
            sys.exit(0)

        click.echo("run command fail.")
        click.echo(command_result)
    sys.exit(-1)


def llm_route(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None,
           auto: Optional[bool] = False):
    with handle_errors():
        model, assistant, content = before_prompt(
            content, parent, reference, instruct, context, model, config_str, None, None, True
		)

        click.echo(assistant.prompt.formatted_header())
        command_result = run_command(
            model_name = model,
            history_messages = assistant.prompt.messages,
            input_text = content,
            parent_hash = parent,
            auto_fun = auto)
        if command_result is not None:
            sys.exit(command_result[0])

        for response in assistant.iterate_response():
            click.echo(response, nl=False)
