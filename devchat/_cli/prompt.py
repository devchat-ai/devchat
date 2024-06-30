import sys
from typing import List, Optional

import click


# 目前接口没有在插件中被使用
# 最初意图：
#  将交互分为两类，1，普通聊天；2，执行一个工作流命令。
# prompt子命令用于普通聊天交互。
# 一些过时的接口：
# -r: 没有被使用，用于选择一个历史聊天上下文；
# -i: AI系统角色描述文件指定，目前应该归属在工作流命令的职责中；
# --config: 没有被使用，用于覆盖默认配置，在命令行交互中可能会有价值；
# --functions: 没有被使用，用于实现函数调用，未来函数调用功能会在工作流命令中实现；
# --function-name: 没有被使用，用户函数调用中返回结果的描述。例如调用AI需要ls命令，下一次将ls结果返回时，需要指明这个结果来自什么函数命令；
# --not-store: 没有被使用，用于指定是否自动保存了解记录到数据库中；
# 其中需要特别关注的是：
# --not-store选项，在命令行交互中，尤其是工作流命令交互中，这个并没有被实现。
# 最初将这个参数独立的原因是：工作流命令涉及较多的准备工作，以及还可能会有其他的参数处理工作，通过
#   devchat-core来启动工作流将是一个安全的选择，所以devchat-core的进程生命周期，不能作为是否用户意图结束的判断依据。
@click.command(help="Interact with the large language model (LLM).")
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
    "-f",
    "--functions",
    type=click.Path(exists=True),
    help="Path to a JSON file with functions for the prompt.",
)
@click.option(
    "-n",
    "--function-name",
    help="Specify the function name when the content is the output of a function.",
)
@click.option(
    "-ns",
    "--not-store",
    is_flag=True,
    default=False,
    required=False,
    help="Do not save the conversation to the store.",
)
def prompt(
    content: Optional[str],
    parent: Optional[str],
    reference: Optional[List[str]],
    instruct: Optional[List[str]],
    context: Optional[List[str]],
    model: Optional[str],
    config_str: Optional[str] = None,
    functions: Optional[str] = None,
    function_name: Optional[str] = None,
    not_store: Optional[bool] = False,
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
    from devchat._cli.router import llm_prompt

    llm_prompt(
        content,
        parent,
        reference,
        instruct,
        context,
        model,
        config_str,
        functions,
        function_name,
        not_store,
    )
    sys.exit(0)
