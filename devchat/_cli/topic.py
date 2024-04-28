import json
# import rich_click as click
from devchat.store import Store
from devchat.openai import OpenAIChatConfig, OpenAIChat
from devchat.utils import get_logger
from devchat._cli.utils import init_dir, handle_errors, get_model_config

from .command import command, Command


logger = get_logger(__name__)


@command('topic', help='Manage topics')
@Command.option('--list', '-l', dest='list_topics', is_flag=True,
              help='List topics in reverse chronological order.')
@Command.option('--skip', default=0, help='Skip number of topics before showing the list.')
@Command.option('-n', '--max-count', default=100, help='Limit the number of topics to output.')
def topic(list_topics: bool, skip: int, max_count: int):
    """
    Manage topics.
    """
    repo_chat_dir, user_chat_dir = init_dir()

    with handle_errors():
        model, config = get_model_config(user_chat_dir)
        parameters_data = config.dict(exclude_unset=True)
        openai_config = OpenAIChatConfig(model=model, **parameters_data)

        chat = OpenAIChat(openai_config)
        store = Store(repo_chat_dir, chat)

        if list_topics:
            topics = store.select_topics(skip, skip + max_count)
            for topic_data in topics:
                try:
                    topic_data.update({'root_prompt': topic_data['root_prompt'].shortlog()})
                except Exception as exc:
                    logger.exception(exc)
                    continue
            print(json.dumps(topics, indent=2))
