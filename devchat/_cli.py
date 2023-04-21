"""
This module contains the main function for the devchat CLI.
"""

from typing import Optional
import json
import click
from pydantic import ValidationError
from devchat.message import Message
from devchat.chat.openai_chat import OpenAIChatConfig, OpenAIChat
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
            chat.prompt([message])
            response_str = json.dumps(chat.complete_response())
        except ValidationError as error:
            response_str = f"Error: {error}"
    else:
        response_str = f"Unknown LLM: {llm}"
    click.echo(response_str)
