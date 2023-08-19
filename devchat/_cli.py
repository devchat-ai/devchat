"""
This module contains the main function for the DevChat CLI.
"""
import json
import sys
import importlib.metadata
import rich_click as click
from devchat.store import Store
from devchat.openai import OpenAIChatConfig, OpenAIChat
from devchat.utils import get_logger
from devchat._cli_prompt import prompt
from devchat._cli_topic import topic
from devchat._cli_utils import handle_errors, init_dir

logger = get_logger(__name__)
click.rich_click.USE_MARKDOWN = True


@click.group()
@click.version_option(importlib.metadata.version("devchat"), '--version',
                      message='DevChat %(version)s')
def main():
    """DevChat CLI: A command-line interface for DevChat."""


@main.command()
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

    config, chat_dir = init_dir()

    with handle_errors():
        provider = config.get('provider')
        if provider == 'OpenAI':
            openai_config = OpenAIChatConfig(model=config['model'], **config['OpenAI'])
            chat = OpenAIChat(openai_config)
            store = Store(chat_dir, chat)
        else:
            click.echo(f"Error: Invalid LLM in configuration '{provider}'", err=True)
            sys.exit(1)

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


main.add_command(prompt)
main.add_command(topic)
