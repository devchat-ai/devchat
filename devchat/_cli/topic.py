import click


# 目前接口在devchat中插件中使用。
# 意图是对topic数据进行管理
# 其中--list参数被使用了。
# 从实际使用情况来说，没有用户会关注很久之前的topic，
# 所以--skip, --max-count参数实际不会被使用，没有实际意义，
# 但从接口完整性角度来说，有理论意义。
@click.command(help="Manage topics")
@click.option(
    "--list", "-l", "list_topics", is_flag=True, help="List topics in reverse chronological order."
)
@click.option("--skip", default=0, help="Skip number of topics before showing the list.")
@click.option("-n", "--max-count", default=100, help="Limit the number of topics to output.")
def topic(list_topics: bool, skip: int, max_count: int):
    """
    Manage topics.
    """
    import json

    from devchat._cli.utils import get_model_config, handle_errors, init_dir
    from devchat.openai import OpenAIChat, OpenAIChatConfig
    from devchat.store import Store

    repo_chat_dir, user_chat_dir = init_dir()

    with handle_errors():
        model, config = get_model_config(user_chat_dir)
        parameters_data = config.dict(exclude_unset=True)
        openai_config = OpenAIChatConfig(model=model, **parameters_data)

        chat = OpenAIChat(openai_config)
        store = Store(repo_chat_dir, chat)

        if list_topics:
            topics = store.select_topics(skip, skip + max_count)
            print(json.dumps(topics, indent=2))
