import json
import sys
import rich_click as click
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig
from devchat.store import Store
from devchat.utils import get_logger
from devchat._cli.utils import handle_errors, init_dir, get_model_config

logger = get_logger(__name__)


@click.command()
@click.option('--skip', default=0, help='Skip number prompts before showing the prompt history.')
@click.option('-n', '--max-count', default=1, help='Limit the number of commits to output.')
@click.option('-t', '--topic', 'topic_root', default=None,
              help='Hash of the root prompt of the topic to select prompts from.')
@click.option('--delete', default=None, help='Delete a leaf prompt from the log.')
def log(skip, max_count, topic_root, delete):
    """
    Manage the prompt history.
    """
    if delete and (skip != 0 or max_count != 1 or topic_root is not None):
        click.echo("Error: The --delete option cannot be used with other options.", err=True)
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
            recent_prompts = store.select_prompts(skip, skip + max_count, topic_root)
            logs = []
            for record in recent_prompts:
                try:
                    logs.append(record.shortlog())
                except Exception as exc:
                    logger.exception(exc)
                    continue
            click.echo(json.dumps(logs, indent=2))
