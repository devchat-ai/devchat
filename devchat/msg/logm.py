from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
import json
import time

from devchat.openai.openai_chat import OpenAIPrompt, OpenAIChat, OpenAIChatConfig
from devchat._cli.utils import get_model_config
from devchat.store import Store

from .path import CHAT_DIR, WORKSPACE_CHAT_DIR
from .util import mock_get_user_info

@dataclass
class PromptData:
    model: str = "none"
    messages: Optional[List[Dict]] = field(default_factory=list)
    parent: Optional[str] = None
    references: Optional[List[str]] = field(default_factory=list)
    timestamp: int = time.time()
    request_tokens: int = 0
    response_tokens: int = 0


def gen_log_prompt(jsondata: Optional[str], filepath: Optional[str]) -> OpenAIPrompt:
    """
    Generate a hash for a chat record
    """    
    print("\$$$$$ enter new insert function $$$$$")
    t0 = time.time()
    prompt_data = PromptData(**json.loads(jsondata))
    user, email = mock_get_user_info()
    prompt = OpenAIPrompt(prompt_data.model, user, email)

    print(f"$$$$$$$ t1: {time.time() - t0}")
    

    prompt.model = prompt_data.model
    prompt.input_messages(prompt_data.messages)
    prompt.parent = prompt_data.parent
    prompt.references = prompt_data.references
    prompt.timestamp = prompt_data.timestamp
    prompt.request_tokens = prompt_data.request_tokens
    prompt.response_tokens = prompt_data.response_tokens

    prompt.finalize_hash()

    return prompt


def insert_log_promt(prompt: OpenAIPrompt) -> Tuple[str, Optional[str]]:
    """
    Insert a chat record

    # TODO: implement the non-blocking way later
    return:
        inserted_hash: insert hash
        error: error message if any
    """
    # TODO: get the dir dynamically
    user_chat_dir = CHAT_DIR
    repo_chat_dir = WORKSPACE_CHAT_DIR
    
    print("\$$$$$ enter new insert function $$$$$")
    t0 = time.time()
    model, config = get_model_config(user_chat_dir)
    openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

    chat = OpenAIChat(openai_config)
    store = Store(repo_chat_dir, chat)
    topic_root = store.store_prompt(prompt)

    print(f"$$$$$$$ t1: {time.time() - t0}")
    print(f"$$$$$$$ Inserted sha: {prompt.hash}")
    return prompt.hash, None



def _do_save_log(user_chat_dir, repo_chat_dir, prompt):
    from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig
    from devchat._cli.utils import get_model_config
    from devchat.store import Store

    model, config = get_model_config(user_chat_dir)
    openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

    chat = OpenAIChat(openai_config)
    store = Store(repo_chat_dir, chat)
    topic_root = store.store_prompt(prompt)