import json
import os
from .baidu_api import complete as baidu_complete, stream_complete as baidu_stream_complete


def to_baidu_message(messages):
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
    return ["ERNIE-Bot", "llama-2-13b-chat"]


def complete(messages, openai_base_config_params, custom_config_params):
    api_key = os.environ.get("BAIDU_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    app_secret = os.environ.get("BAIDU_APP_SECRET")

    temperature = 0.95

    if custom_config_params:
        if custom_config_params.temperature:
            temperature = custom_config_params.temperature
        if not custom_config_params.api_secret and not app_secret:
            raise ValueError("api_secret is required for xinghuo model")
        if custom_config_params.api_secret:
            app_secret = custom_config_params.api_secret

    question = to_baidu_message(messages)

    model = openai_base_config_params["model"]
    response = baidu_complete(model, api_key, app_secret, question, temperature)
    return json.dumps(response)


def stream_complete(messages, openai_base_config_params, custom_config_params):
    api_key = os.environ.get("BAIDU_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    app_secret = os.environ.get("BAIDU_APP_SECRET")

    temperature = 0.95

    if custom_config_params:
        if custom_config_params.temperature:
            temperature = custom_config_params.temperature
        if not custom_config_params.api_secret and not app_secret:
            raise ValueError("api_secret is required for xinghuo model")
        if custom_config_params.api_secret:
            app_secret = custom_config_params.api_secret

    question = to_baidu_message(messages)

    model = openai_base_config_params["model"]
    stream_response = baidu_stream_complete(model, api_key, app_secret, question, temperature)
    return stream_response
