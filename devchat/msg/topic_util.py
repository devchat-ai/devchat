import os
from typing import Dict, List, Optional

from devchat._cli.utils import get_model_config
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig
from devchat.store import Store
from devchat.workspace_util import USER_CHAT_DIR, get_workspace_chat_dir


def get_topic_shortlogs(
    topic_root_hash: str, limit: int, offset: int, workspace_path: Optional[str]
) -> List[Dict]:
    short_logs = []

    user_chat_dir = USER_CHAT_DIR
    workspace_chat_dir = get_workspace_chat_dir(workspace_path)

    model, config = get_model_config(user_chat_dir)
    openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

    chat = OpenAIChat(openai_config)
    store = Store(workspace_chat_dir, chat)

    logs = store.select_prompts(offset, offset + limit, topic_root_hash)
    for log in logs:
        try:
            short_logs.append(log.shortlog())
        except Exception:
            # TODO: log the error
            continue

    return short_logs


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
        # filter out deleted topics
        record_file = os.path.join(workspace_chat_dir, ".deletedTopics")
        if os.path.exists(record_file):
            with open(record_file, "r") as f:
                deleted_topics = f.read().split("\n")

            topics = [t for t in topics if t["root_prompt"]["hash"] not in deleted_topics]

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
