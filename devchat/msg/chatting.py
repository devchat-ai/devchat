from typing import Optional, Iterator
import json

from devchat._cli.errors import MissContentInPromptException
from devchat._cli.utils import init_dir
from devchat.assistant import Assistant
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig
from devchat.store import Store
from devchat.utils import parse_files

from .schema import MessageRequest
from .path import CHAT_DIR, WORKSPACE_CHAT_DIR

from devchat._cli.utils import get_model_config


def _get_model_and_config(model: Optional[str], config_str: Optional[str]):

    model, config = get_model_config(CHAT_DIR, model)

    parameters_data = config.dict(exclude_unset=True)
    if config_str:
        config_data = json.loads(config_str)
        parameters_data.update(config_data)
    return model, parameters_data


def chatting(msg: MessageRequest) -> Iterator[str]:
    context = msg.context
    content = msg.content
    parent = msg.parent
    model = msg.model_name
    print("enter chatting")

    repo_chat_dir = WORKSPACE_CHAT_DIR

    context_contents = parse_files(context)

    model, parameters_data = _get_model_and_config(model, None)
    max_input_tokens = parameters_data.get("max_input_tokens", 4000)

    openai_config = OpenAIChatConfig(model=model, **parameters_data)
    chat = OpenAIChat(openai_config)
    chat_store = Store(repo_chat_dir, chat)

    # assistant = Assistant(chat, chat_store, max_input_tokens, not not_store)
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

    print("assistant.make_prompt done")
    for res in assistant.iterate_response():
    # for res in _mock_txt_res():
        print(res, end="", flush=True)
        yield res

def _mock_txt_res():
    import time
    sample_txt = """
床前明月光，
疑是地上霜。
举头望明月，
低头思故乡。
"""
    lines = sample_txt.split("\n")
    for line in lines:
        time.sleep(0.5)
        yield line + "\n\n"