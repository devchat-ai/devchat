import json
import os
from .anthropic_api import (\
	complete as anthropic_complete,\
	stream_complete as anthropic_stream_complete)


def to_anthropic_message(messages):
    for index, _ in enumerate(messages):
        if messages[index]["role"] not in ["user", "assistant"]:
            messages[index]["role"] = "user"

    messages_new = []
    for message in messages:
        if len(messages_new) >= 1 and messages_new[-1]["role"] == message["role"]:
            messages_new[-1]["content"] += message["content"]
        else:
            messages_new.append(message)
    return messages_new


def supported_models():
    return ["claude-2"]


def complete(messages, openai_base_config_params, custom_config_params): # pylint: disable=unused-argument
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    temperature = 0.3
    max_tokens = 150

    if custom_config_params:
        if custom_config_params.temperature:
            temperature = custom_config_params.temperature
        if custom_config_params.max_tokens:
            max_tokens = custom_config_params.max_tokens

    question = to_anthropic_message(messages)

    response = anthropic_complete(api_key, question, temperature, max_tokens)
    return json.dumps(response)


def stream_complete(messages, openai_base_config_params, custom_config_params): # pylint: disable=unused-argument
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    temperature = 0.3
    max_tokens = 150

    if custom_config_params:
        if custom_config_params.temperature:
            temperature = custom_config_params.temperature
        if custom_config_params.max_tokens:
            max_tokens = custom_config_params.max_tokens

    question = to_anthropic_message(messages)

    stream_response = anthropic_stream_complete(api_key, question, temperature, max_tokens)
    return stream_response
