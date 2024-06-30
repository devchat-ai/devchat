import sys
from typing import List, Optional

import click


# 目前接口在devchat中插件中使用。
# 用途：根据用户输入，自动判断是否为工作流命令或者普通聊天，执行对应的操作。
# 相当于是run,和prompt命令的自动路由接口。
#
# -r: 用于指定需要引用的某个聊天上下文（用户问题，AI回答），目前没有被使用，实际命令行交互中更难被使用。
#     预期未来不会被使用到。
# -i: 基于工作流的机制，AI角色描述会在工作流中实现，如果仅仅有角色描述，那么就是很简单的工作流，自定义
#     角色描述。
# --config: 预期保留用于命令行交互使用，目前IDE插件中没有对应的使用。
# -a: 没有被使用。
@click.command(help="Route a prompt to the specified LLM")
@click.argument("content", required=False)
@click.option("-p", "--parent", help="Input the parent prompt hash to continue the conversation.")
@click.option(
    "-r",
    "--reference",
    multiple=True,
    help="Input one or more specific previous prompts to include in the current prompt.",
)
@click.option(
    "-i", "--instruct", multiple=True, help="Add one or more files to the prompt as instructions."
)
@click.option(
    "-c", "--context", multiple=True, help="Add one or more files to the prompt as a context."
)
@click.option("-m", "--model", help="Specify the model to use for the prompt.")
@click.option(
    "--config",
    "config_str",
    help="Specify a JSON string to overwrite the default configuration for this prompt.",
)
@click.option(
    "-a",
    "--auto",
    is_flag=True,
    default=False,
    required=False,
    help="Answer question by function-calling.",
)
def route(
    content: Optional[str],
    parent: Optional[str],
    reference: Optional[List[str]],
    instruct: Optional[List[str]],
    context: Optional[List[str]],
    model: Optional[str],
    config_str: Optional[str] = None,
    auto: Optional[bool] = False,
):
    """
    This command performs interactions with the specified large language model (LLM)
    by sending prompts and receiving responses.

    Examples
    --------

    To send a multi-line message to the LLM, use the here-doc syntax:

    ```bash
    devchat prompt << 'EOF'
    What is the capital of France?
    Can you tell me more about its history?
    EOF
    ```

    Note the quotes around EOF in the first line, to prevent the shell from expanding variables.

    Configuration
    -------------

    DevChat CLI reads configuration from `~/.chat/config.yml`
    (if `~/.chat` is not accessible, it will try `.chat` in your current Git or SVN root directory).
    You can edit the file to modify default configuration.

    To use OpenAI's APIs, you have to set an API key by the environment variable `OPENAI_API_KEY`.
    Run the following command line with your API key:

    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

    """
    from devchat._cli.router import llm_route

    llm_route(content, parent, reference, instruct, context, model, config_str, auto)
    sys.exit(0)
