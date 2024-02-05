import json
import sys
from typing import List, Optional
import rich_click as click
from devchat.engine import run_command
from devchat.assistant import Assistant
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig
from devchat.store import Store
from devchat.utils import parse_files
from devchat._cli.utils import handle_errors, init_dir, get_model_config



def before_prompt(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None,
           functions: Optional[str] = None, function_name: Optional[str] = None,
           not_store: Optional[bool] = False):
    repo_chat_dir, user_chat_dir = init_dir()

    if content is None:
        content = click.get_text_stream('stdin').read()

    if content == '':
        return None, None, None, None, None

    instruct_contents = parse_files(instruct)
    context_contents = parse_files(context)

    model, config = get_model_config(repo_chat_dir, user_chat_dir, model)

    parameters_data = config.dict(exclude_unset=True)
    if config_str:
        config_data = json.loads(config_str)
        parameters_data.update(config_data)
    openai_config = OpenAIChatConfig(model=model, **parameters_data)

    chat = OpenAIChat(openai_config)
    chat_store = Store(repo_chat_dir, chat)

    assistant = Assistant(chat, chat_store, config.max_input_tokens, not not_store)

    functions_data = None
    if functions is not None:
        with open(functions, 'r', encoding="utf-8") as f_file:
            functions_data = json.load(f_file)
    assistant.make_prompt(content, instruct_contents, context_contents, functions_data,
                            parent=parent, references=reference,
                            function_name=function_name)
    return openai_config, model, assistant, content, context_contents



def llm_prompt(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None,
           functions: Optional[str] = None, function_name: Optional[str] = None,
           not_store: Optional[bool] = False):
    with handle_errors():
        _1, _2, assistant, _3, _4 = before_prompt(
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
        openai_config, model, assistant, content, _1 = before_prompt(
            content, parent, reference, instruct, context, model, config_str, None, None, True
		)

        click.echo(assistant.prompt.formatted_header())
        command_result = run_command(
            openai_config,
            model,
            assistant.prompt.messages,
            content,
            parent,
            False)
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
        openai_config, model, assistant, content, _1 = before_prompt(
            content, parent, reference, instruct, context, model, config_str, None, None, True
		)

        click.echo(assistant.prompt.formatted_header())
        command_result = run_command(
            openai_config,
            model,
            assistant.prompt.messages,
            content,
            parent,
            auto)
        if command_result is not None:
            sys.exit(command_result[0])

        for response in assistant.iterate_response():
            click.echo(response, nl=False)
