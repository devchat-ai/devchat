import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from devchat._cli.utils import get_model_config
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig, OpenAIPrompt
from devchat.store import Store
from devchat.workspace_util import USER_CHAT_DIR, get_workspace_chat_dir

from .user_info import user_info


@dataclass
class PromptData:
    model: str = "none"
    messages: Optional[List[Dict]] = field(default_factory=list)
    parent: Optional[str] = None
    references: Optional[List[str]] = field(default_factory=list)
    timestamp: int = time.time()
    request_tokens: int = 0
    response_tokens: int = 0


def gen_log_prompt(jsondata: Optional[str] = None, filepath: Optional[str] = None) -> OpenAIPrompt:
    """
    Generate a hash for a chat record
    """
    assert jsondata is not None or filepath is not None, "Either jsondata or filepath is required."

    if jsondata is None:
        with open(filepath, "r", encoding="utf-8") as f:
            jsondata = f.read()

    prompt_data = PromptData(**json.loads(jsondata))
    name = user_info.name
    email = user_info.email
    prompt = OpenAIPrompt(prompt_data.model, name, email)

    prompt.model = prompt_data.model
    prompt.input_messages(prompt_data.messages)
    prompt.parent = prompt_data.parent
    prompt.references = prompt_data.references
    prompt.timestamp = prompt_data.timestamp
    prompt.request_tokens = prompt_data.request_tokens
    prompt.response_tokens = prompt_data.response_tokens

    prompt.finalize_hash()

    return prompt


def insert_log_prompt(prompt: OpenAIPrompt, workspace_path: Optional[str]) -> str:
    """
    Insert a chat record

    return the hash of the inserted chat record (prompt)
    """
    user_chat_dir = USER_CHAT_DIR
    workspace_chat_dir = get_workspace_chat_dir(workspace_path)

    model, config = get_model_config(user_chat_dir)
    openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

    chat = OpenAIChat(openai_config)
    store = Store(workspace_chat_dir, chat)
    _ = store.store_prompt(prompt)

    return prompt.hash


def delete_log_prompt(hash: str, workspace_path: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Delete a chat record

    return:
        success: True if the prompt is deleted successfully, False otherwise
    """
    user_chat_dir = USER_CHAT_DIR
    workspace_chat_dir = get_workspace_chat_dir(workspace_path)

    model, config = get_model_config(user_chat_dir)
    openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

    chat = OpenAIChat(openai_config)
    store = Store(workspace_chat_dir, chat)

    success = store.delete_prompt(hash)

    return success
