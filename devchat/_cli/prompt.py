import json
from typing import List, Optional
import rich_click as click
from devchat.assistant import Assistant
from devchat.openai.openai_chat import OpenAIChat, OpenAIChatConfig
from devchat.store import Store
from devchat.utils import parse_files
from devchat._cli.utils import handle_errors, init_dir, get_model_config


@click.command()
@click.argument('content', required=False)
@click.option('-p', '--parent', help='Input the parent prompt hash to continue the conversation.')
@click.option('-r', '--reference', multiple=True,
              help='Input one or more specific previous prompts to include in the current prompt.')
@click.option('-i', '--instruct', multiple=True,
              help='Add one or more files to the prompt as instructions.')
@click.option('-c', '--context', multiple=True,
              help='Add one or more files to the prompt as a context.')
@click.option('-m', '--model', help='Specify the model to use for the prompt.')
@click.option('--config', 'config_str',
              help='Specify a JSON string to overwrite the default configuration for this prompt.')
@click.option('-f', '--functions', type=click.Path(exists=True),
              help='Path to a JSON file with functions for the prompt.')
@click.option('-n', '--function-name',
              help='Specify the function name when the content is the output of a function.')
def prompt(content: Optional[str], parent: Optional[str], reference: Optional[List[str]],
           instruct: Optional[List[str]], context: Optional[List[str]],
           model: Optional[str], config_str: Optional[str] = None,
           functions: Optional[str] = None, function_name: Optional[str] = None):
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
    repo_chat_dir, user_chat_dir = init_dir()

    with handle_errors():
        if content is None:
            content = click.get_text_stream('stdin').read()

        if content == '':
            return

        instruct_contents = parse_files(instruct)
        context_contents = parse_files(context)

        model, config = get_model_config(repo_chat_dir, user_chat_dir, model)

        parameters_data = config.dict(exclude_unset=True)
        if config_str:
            config_data = json.loads(config_str)
            parameters_data.update(config_data)
        openai_config = OpenAIChatConfig(model=model, **parameters_data)

        chat = OpenAIChat(openai_config)
        store = Store(repo_chat_dir, chat)

        assistant = Assistant(chat, store, config.max_input_tokens)

        functions_data = None
        if functions is not None:
            with open(functions, 'r', encoding="utf-8") as f_file:
                functions_data = json.load(f_file)
        assistant.make_prompt(content, instruct_contents, context_contents, functions_data,
                              parent=parent, references=reference,
                              function_name=function_name)

        for response in assistant.iterate_response():
            click.echo(response, nl=False)
