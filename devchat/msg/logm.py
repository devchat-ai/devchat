from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
import json
import time
import os

from devchat.openai.openai_chat import OpenAIPrompt, OpenAIChat, OpenAIChatConfig
from devchat._cli.utils import get_model_config
from devchat.store import Store

from .util import get_workspace_chat_dir, USER_CHAT_DIR
from .user_info import user_info
from .schema import MessageRequest


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
    t0 = time.time()
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


def insert_log_prompt(
    prompt: OpenAIPrompt, workspace_path: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Insert a chat record

    return:
        inserted_hash: insert hash
        error: error message if any
    """
    inserted_hash = None
    error_msg = None

    try:

        user_chat_dir = USER_CHAT_DIR
        workspace_chat_dir = get_workspace_chat_dir(workspace_path)

        model, config = get_model_config(user_chat_dir)
        openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

        chat = OpenAIChat(openai_config)
        store = Store(workspace_chat_dir, chat)
        _ = store.store_prompt(prompt)

        inserted_hash = prompt.hash
    except Exception as e:
        error_msg = str(e)

    return inserted_hash, error_msg


def delete_log_prompt(
    hash: str, workspace_path: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """
    Delete a chat record

    return:
        success: True if the prompt is deleted successfully, False otherwise
        error: error message if any
    """
    success = False
    error_msg = None

    try:
        user_chat_dir = USER_CHAT_DIR
        workspace_chat_dir = get_workspace_chat_dir(workspace_path)

        model, config = get_model_config(user_chat_dir)
        openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

        chat = OpenAIChat(openai_config)
        store = Store(workspace_chat_dir, chat)

        success = store.delete_prompt(hash)

        if not success:
            error_msg = f"Failed to delete prompt {hash}."
    except Exception as e:
        error_msg = str(e)

    return success, error_msg


def get_topic_shortlogs(
    topic_root_hash: str, limit: int, offset: int, workspace_path: Optional[str]
) -> Tuple[List[Dict], Optional[str]]:
    short_logs = []
    error_msg = None
    try:
        user_chat_dir = USER_CHAT_DIR
        workspace_chat_dir = get_workspace_chat_dir(workspace_path)

        model, config = get_model_config(user_chat_dir)
        openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

        chat = OpenAIChat(openai_config)
        store = Store(workspace_chat_dir, chat)

        logs = store.select_prompts(offset, offset + limit, topic_root_hash)
        for l in logs:
            try:
                short_logs.append(l.shortlog())
            except Exception as e:
                # TODO: log the error
                continue

    except Exception as e:
        error_msg = str(e)

    return short_logs, error_msg


def get_topics(
    limit: int, offset: int, workspace_path: Optional[str], with_deleted: bool = False
) -> List[Dict]:
    topics = []

    user_chat_dir = USER_CHAT_DIR
    workspace_chat_dir = get_workspace_chat_dir(workspace_path)

    model, config = get_model_config(user_chat_dir)
    openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

    chat = OpenAIChat(openai_config)
    store = Store(workspace_chat_dir, chat)

    topics = store.select_topics(offset, offset + limit)

    if not with_deleted:
        record_file = os.path.join(workspace_chat_dir, ".deletedTopics")
        if os.path.exists(record_file):
            with open(record_file, "r") as f:
                deleted_topics = f.read().split("\n")
            topics = [
                t for t in topics if t["root_prompt"]["hash"] not in deleted_topics
            ]

    return topics


def delete_topic(topic_hash: str, workspace_path: Optional[str]):
    """
    Logicalily delete a topic
    """
    workspace_chat_dir = get_workspace_chat_dir(workspace_path)

    record_file = os.path.join(workspace_chat_dir, ".deletedTopics")
    if not os.path.exists(record_file):
        with open(record_file, "w") as f:
            f.write(topic_hash)
    else:
        with open(record_file, "a") as f:
            f.write(f"\n{topic_hash}")

    return
