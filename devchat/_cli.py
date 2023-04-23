"""
This module contains the main function for the devchat CLI.
"""

from typing import Optional
import json
import click
from pydantic import ValidationError
from devchat.message import Message
from devchat.chat.openai_chat import OpenAIChatConfig, OpenAIChat
from devchat.prompt import Prompt
from devchat.utils import is_valid_hash


@click.command()
@click.option('-r', '--reference', default='', help='Reference to prompt IDs')
@click.argument('content')
def main(content: str, reference: Optional[str]):
    """
    Main function to run the chat application with the specified configuration file.

    This function reads the configuration file, initializes the chat system based on the
    specified large language model (LLM), and performs interactions with the user by sending prompts
    and retrieving responses. If the LLM is not recognized, it will print an error message.

    Args:
        content (str): One or more lines of text for the Message object.
        reference (str): Reference to prompt IDs.
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

    message = Message("user", content)
    if reference:
        # split the reference argument by comma and strip whitespace
        hash_values = [value.strip() for value in reference.split(',') if value.strip()]

        # validate the hash values and handle errors accordingly
        for value in hash_values:
            if not is_valid_hash(value):
                click.echo(f"Invalid hash value: {value}")

    llm = config_data.get('llm')

    if llm == 'OpenAI':
        try:
            openai_config = OpenAIChatConfig(**config_data['OpenAI'])
            chat = OpenAIChat(openai_config)
            prompt = Prompt(chat.config.model)
            chat.prompt([message])

            if openai_config.stream:
                response_iterator = chat.stream_response()
                for response_chunk in response_iterator:
                    delta_str = prompt.append_response(str(response_chunk))
                    if delta_str is None:
                        click.echo()
                    else:
                        click.echo(delta_str, nl=False)
                for i in range(1, len(prompt.responses)):
                    click.echo(f"[{i}]: {prompt.responses[i].content}")

            else:
                response_str = str(chat.complete_response())
                prompt.set_response(response_str)
                if len(prompt.responses) == 1:
                    click.echo(prompt.responses[0].content)
                else:
                    for index, response in prompt.responses.items():
                        click.echo(f"[{index}]: {response.content}")

        except ValidationError as error:
            click.echo(f"Error: {error}")
    else:
        click.echo(f"Unknown LLM: {llm}")
