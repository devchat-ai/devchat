import sys
from typing import List, Optional

import click


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
