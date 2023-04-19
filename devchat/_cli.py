"""
This module contains the main function for the devchat CLI.
"""

import json
import click
from pydantic import ValidationError
from devchat.chat.openai_chat import OpenAIChatConfig, OpenAIChat

@click.command()
@click.argument('config_file', type=click.Path(exists=True, readable=True))
def main(config_file):
    with open(config_file, 'r', encoding='utf-8') as file:
        config_data = json.load(file)

    llm = config_data.get('llm', 'OpenAI')  # Default to OpenAI if not specified

    if llm == 'OpenAI':
        try:
            openai_config = OpenAIChatConfig(**config_data['OpenAI'])
            chat = OpenAIChat(openai_config)
            chat.prompt("Hello!")
            chat.complete_response()
            click.echo(f"Config: {openai_config}")
        except ValidationError as error:
            click.echo(f"Error: {error}")
    else:
        click.echo(f"Unknown LLM: {llm}")
