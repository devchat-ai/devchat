import json
import sys
import rich_click as click
from devchat.store import Store
from devchat.openai import OpenAIChatConfig, OpenAIChat
from devchat.utils import get_logger
from devchat._cli.utils import init_dir, handle_errors

logger = get_logger(__name__)


@click.command()
@click.option('--list', '-l', 'list_topics', is_flag=True,
              help='List topics in reverse chronological order.')
@click.option('--skip', default=0, help='Skip number of topics before showing the list.')
@click.option('-n', '--max-count', default=100, help='Limit the number of topics to output.')
def topic(list_topics: bool, skip: int, max_count: int):
    """
    Manage topics.
    """
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

        if list_topics:
            topics = store.select_topics(skip, skip + max_count)
            for topic_data in topics:
                try:
                    topic_data.update({'root_prompt': topic_data['root_prompt'].shortlog()})
                except Exception as exc:
                    logger.exception(exc)
                    continue
            click.echo(json.dumps(topics, indent=2))
