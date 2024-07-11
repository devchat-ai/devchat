import json
from typing import Iterator, List, Optional

from devchat._cli.utils import get_model_config
from devchat.assistant import Assistant
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig
from devchat.path import USER_CHAT_DIR
from devchat.store import Store
from devchat.utils import parse_files
from devchat.workspace_util import get_workspace_chat_dir


def _get_model_and_config(model: Optional[str], config_str: Optional[str]):
    model, config = get_model_config(USER_CHAT_DIR, model)

    parameters_data = config.dict(exclude_unset=True)
    if config_str:
        config_data = json.loads(config_str)
        parameters_data.update(config_data)
    return model, parameters_data


def chatting(
    content: str,
    model_name: str,
    parent: Optional[str],
    workspace: Optional[str],
    context_files: Optional[List[str]],
) -> Iterator[str]:
    workspace_chat_dir = get_workspace_chat_dir(workspace)

    context_contents = parse_files(context_files)

    model, parameters_data = _get_model_and_config(model_name, None)
    max_input_tokens = parameters_data.get("max_input_tokens", 4000)

    openai_config = OpenAIChatConfig(model=model, **parameters_data)
    chat = OpenAIChat(openai_config)
    chat_store = Store(workspace_chat_dir, chat)

    assistant = Assistant(
        chat=chat,
        store=chat_store,
        max_prompt_tokens=max_input_tokens,
        need_store=False,
    )
    assistant.make_prompt(
        request=content,
        instruct_contents=None,
        context_contents=context_contents,
        functions=None,
        parent=parent,
        references=None,
        function_name=None,
    )

    for res in assistant.iterate_response():
        yield res
