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
    """
    Main function to run the chat application with the specified configuration file.
    
    This function reads the configuration file, initializes the chat system based on the
    specified large language model (LLM), and performs interactions with the user by sending prompts
    and retrieving responses. If the LLM is not recognized, it will print an error message.
    
    Args:
        config_file (str): Path to the JSON configuration file containing LLM and API settings.
        
    Raises:
        ValidationError: If there's a validation error in the configuration data.
    """
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
