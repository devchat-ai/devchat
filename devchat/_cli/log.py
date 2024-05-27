import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import click


@dataclass
class PromptData:
    model: str = "none"
    messages: Optional[List[Dict]] = field(default_factory=list)
    parent: Optional[str] = None
    references: Optional[List[str]] = field(default_factory=list)
    timestamp: int = time.time()
    request_tokens: int = 0
    response_tokens: int = 0


@click.command(help="Process logs")
@click.option("--skip", default=0, help="Skip number prompts before showing the prompt history.")
@click.option("-n", "--max-count", default=1, help="Limit the number of commits to output.")
@click.option(
    "-t",
    "--topic",
    "topic_root",
    default=None,
    help="Hash of the root prompt of the topic to select prompts from.",
)
@click.option("--insert", default=None, help="JSON string of the prompt to insert into the log.")
@click.option("--delete", default=None, help="Hash of the leaf prompt to delete from the log.")
def log(skip, max_count, topic_root, insert, delete):
    """
    Manage the prompt history.
    """
    from devchat._cli.utils import get_model_config, handle_errors, init_dir
    from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig, OpenAIPrompt
    from devchat.store import Store
    from devchat.utils import get_logger, get_user_info

    logger = get_logger(__name__)

    # handler insert
    # if insert is a file path, then read file content as "insert" value, then delete that file
    try:
        if os.path.isfile(insert):
            insert_file = insert
            with open(insert_file, "r", encoding="utf-8") as f:
                insert = f.read()
            os.remove(insert_file)
    except Exception:
        pass

    if (insert or delete) and (skip != 0 or max_count != 1 or topic_root is not None):
        print(
            "Error: The --insert or --delete option cannot be used with other options.",
            file=sys.stderr,
        )
        sys.exit(1)

    repo_chat_dir, user_chat_dir = init_dir()

    with handle_errors():
        model, config = get_model_config(user_chat_dir)
        openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

        chat = OpenAIChat(openai_config)
        store = Store(repo_chat_dir, chat)

        if delete:
            success = store.delete_prompt(delete)
            if success:
                print(f"Prompt {delete} deleted successfully.")
            else:
                print(f"Failed to delete prompt {delete}.")
        else:
            if insert:
                prompt_data = PromptData(**json.loads(insert))
                user, email = get_user_info()
                prompt = OpenAIPrompt(prompt_data.model, user, email)
                prompt.model = prompt_data.model
                prompt.input_messages(prompt_data.messages)
                prompt.parent = prompt_data.parent
                prompt.references = prompt_data.references
                prompt.timestamp = prompt_data.timestamp
                prompt.request_tokens = prompt_data.request_tokens
                prompt.response_tokens = prompt_data.response_tokens
                topic_root = store.store_prompt(prompt)

            recent_prompts = store.select_prompts(skip, skip + max_count, topic_root)
            logs = []
            for record in recent_prompts:
                try:
                    logs.append(record.shortlog())
                except Exception as exc:
                    logger.exception(exc)
                    continue
            print(json.dumps(logs, indent=2))
