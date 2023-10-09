import json
import sys
from typing import Optional, List, Dict
from pydantic import BaseModel
import rich_click as click
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig, OpenAIPrompt
from devchat.store import Store
from devchat.utils import get_logger, get_user_info
from devchat._cli.utils import handle_errors, init_dir, get_model_config


class PromptData(BaseModel):
    model: str
    messages: List[Dict]
    parent: Optional[str] = None
    references: Optional[List[str]] = []
    timestamp: int
    request_tokens: int
    response_tokens: int


logger = get_logger(__name__)


@click.command()
@click.option('--skip', default=0, help='Skip number prompts before showing the prompt history.')
@click.option('-n', '--max-count', default=1, help='Limit the number of commits to output.')
@click.option('-t', '--topic', 'topic_root', default=None,
              help='Hash of the root prompt of the topic to select prompts from.')
@click.option('--insert', default=None, help='JSON string of the prompt to insert into the log.')
@click.option('--delete', default=None, help='Hash of the leaf prompt to delete from the log.')
def log(skip, max_count, topic_root, insert, delete):
    """
    Manage the prompt history.
    """
    if (insert or delete) and (skip != 0 or max_count != 1 or topic_root is not None):
        click.echo("Error: The --insert or --delete option cannot be used with other options.",
                   err=True)
        sys.exit(1)

    repo_chat_dir, user_chat_dir = init_dir()

    with handle_errors():
        model, config = get_model_config(repo_chat_dir, user_chat_dir)
        openai_config = OpenAIChatConfig(model=model, **config.dict(exclude_unset=True))

        chat = OpenAIChat(openai_config)
        store = Store(repo_chat_dir, chat)

        if delete:
            success = store.delete_prompt(delete)
            if success:
                click.echo(f"Prompt {delete} deleted successfully.")
            else:
                click.echo(f"Failed to delete prompt {delete}.")
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
                store.store_prompt(prompt)

            recent_prompts = store.select_prompts(skip, skip + max_count, topic_root)
            logs = []
            for record in recent_prompts:
                try:
                    logs.append(record.shortlog())
                except Exception as exc:
                    logger.exception(exc)
                    continue
            click.echo(json.dumps(logs, indent=2))
