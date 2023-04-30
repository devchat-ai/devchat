"""
This module contains the main function for the DevChat CLI.
"""


import os
import time
from typing import Optional
import json
import sys
from contextlib import contextmanager
import rich_click as click
from devchat.message import MessageType
from devchat.openai import OpenAIMessage
from devchat.openai import OpenAIPrompt
from devchat.openai import OpenAIChatConfig, OpenAIChat
from devchat.utils import get_git_user_info, parse_files, is_valid_hash


click.rich_click.USE_MARKDOWN = True


@click.group()
def main():
    """DevChat CLI: A command-line interface for the DevChat chatbot."""


@contextmanager
def handle_errors():
    """Handle errors in the CLI."""
    try:
        yield
    except Exception as error:
        click.echo(f"Error: {error}", err=True)
        sys.exit(os.EX_SOFTWARE)


@main.command()
@click.argument('content', required=False)
@click.option('-p', '--parent', help='Input the previous prompt hash to continue the conversation.')
@click.option('-r', '--reference', help='Input one or more specific previous prompt hashes to '
              'include in the current prompt.')
@click.option('--instruct', help='Add one or more files to the prompt as instructions.')
@click.option('--context', help='Add one or more files to the prompt as a context.')
def prompt(content: Optional[str], parent: Optional[str], reference: Optional[str],
           instruct: Optional[str], context: Optional[str]):
    """
    Main function to run the chat application.

    This function initializes the chat system based on the specified large language model (LLM),
    and performs interactions with the user by sending prompts and retrieving responses.

    Examples
    --------

    To send a single-line message to the LLM, provide the content as an argument:

    ```bash
    devchat prompt "What is the capital of France?"
    ```

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

    The DevChat CLI reads its configuration from a file `.chatconfig.json` in the current directory.
    If the file is not found, it uses the following default configuration:
    ```json
    {
        "llm": "OpenAI",
        "OpenAI": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.2
        }
    }
    ```

    To customize the configuration, create a `.chatconfig.json` file in the current directory and
    modify the settings as needed. We recoommend the following settings:
    ```json
    {
        "llm": "OpenAI",
        "OpenAI": {
            "model": "gpt-4",
            "temperature": 0.2,
            "stream": true
        }
    }
    ```

    Note: To use OpenAI's APIs, you must have an API key to run the CLI.
    Run the following command line with your API key:

    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

    """
    default_config_data = {
        'llm': 'OpenAI',
        'OpenAI': {
            'model': 'gpt-3.5-turbo',
            'temperature': 0.2
        }
    }

    try:
        with open('.chatconfig.json', 'r', encoding='utf-8') as file:
            config_data = json.load(file)
    except FileNotFoundError:
        config_data = default_config_data

    with handle_errors():
        if content is None:
            content = click.get_text_stream('stdin').read()

        if content == '':
            return

        instruct_contents = parse_files(instruct)
        context_contents = parse_files(context)

        llm = config_data.get('llm')

        if parent is not None:
            for parent_hash in parent.split(','):
                if not is_valid_hash(parent_hash):
                    click.echo(f"Error: Invalid prompt hash '{parent_hash}'.", err=True)
                    sys.exit(os.EX_DATAERR)

        if reference is not None:
            for reference_hash in reference.split(','):
                if not is_valid_hash(reference_hash):
                    click.echo(f"Error: Invalid prompt hash '{reference_hash}'.", err=True)
                    sys.exit(os.EX_DATAERR)

        if llm == 'OpenAI':
            openai_config = OpenAIChatConfig(**config_data['OpenAI'])
            chat = OpenAIChat(openai_config)
            user, email = get_git_user_info()
            openai_prompt = OpenAIPrompt(chat.config.model, user, email)

            # Add instructions to the prompt
            if instruct_contents:
                combined_instruct = ''.join(instruct_contents)
                if not combined_instruct:
                    raise ValueError('Empty instructions.')
                message = OpenAIMessage(MessageType.INSTRUCT, "system", combined_instruct)
                openai_prompt.append_message(message)
            # Add user request
            message = OpenAIMessage(MessageType.INSTRUCT, "user", content)
            openai_prompt.append_message(message)
            # Add context to the prompt
            if context_contents:
                message = OpenAIMessage(MessageType.INSTRUCT, "user", "The context is as follows.")
                for context_content in context_contents:
                    message = OpenAIMessage(MessageType.CONTEXT, "user", context_content)
                    openai_prompt.append_message(message)
            chat.request(openai_prompt)

            if openai_config.stream:
                response_iterator = chat.stream_response()
                for chunk in response_iterator:
                    delta_str = openai_prompt.append_response(str(chunk))
                    click.echo(delta_str, nl=False)
                click.echo(f'\n\nprompt {openai_prompt.hash(0)}\n')
                for index in range(1, len(openai_prompt.responses)):
                    click.echo(openai_prompt.formatted_response(index) + '\n')
            else:
                response_str = str(chat.complete_response())
                openai_prompt.set_response(response_str)
                for index in openai_prompt.responses.keys():
                    click.echo(openai_prompt.formatted_response(index) + '\n')
        else:
            click.echo(f"Error: Invalid LLM in configuration '{llm}'. Expected 'OpenAI'.", err=True)
            sys.exit(os.EX_DATAERR)


@main.command()
@click.option('--skip', default=0, help='Skip number prompts before showing the prompt history.')
@click.option('--max-count', default=100, help='Limit the number of commits to output.')
def log(skip, max_count):
    """
    Show the prompt history.
    """
    # Implement the logic to display the prompt history based on the `skip` and `max_count` options.
    logs = []
    for index in range(skip, skip + max_count):
        message = OpenAIMessage(MessageType.CONTEXT, "user", f"Prompt {index}")
        name, email = get_git_user_info()
        openai_prompt = OpenAIPrompt("gpt-3.5-turbo", name, email)
        openai_prompt.append_message(message)
        response = {
            "model": "gpt-3.5-turbo-0301",
            "created": int(time.time()),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Response {index}",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        }
        openai_prompt.set_response(json.dumps(response))
        logs = openai_prompt.shortlog() + logs
    click.echo(json.dumps(logs))
