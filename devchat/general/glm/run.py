import json
import os
from .glm_api import complete as glm_complete, stream_complete as glm_stream_complete


def to_glm_message(messages):
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
    return ["chatglm_pro"]


def complete(messages, openai_base_config_params, custom_config_params):
    model_name = openai_base_config_params["model"]
    api_key = os.environ.get("ZHIPUAI_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    temperature = 0.95
    top_p = 0.7

    if custom_config_params:
        if custom_config_params.temperature:
            temperature = custom_config_params.temperature
        if custom_config_params.top_p:
            top_p = custom_config_params.top_p

    question = to_glm_message(messages)

    response = glm_complete(api_key, model_name, question, temperature, top_p)
    return json.dumps(response)


def stream_complete(messages, openai_base_config_params, custom_config_params):
    model_name = openai_base_config_params["model"]
    api_key = os.environ.get("ZHIPUAI_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    temperature = 0.95
    top_p = 0.7

    if custom_config_params:
        if custom_config_params.temperature:
            temperature = custom_config_params.temperature
        if custom_config_params.top_p:
            top_p = custom_config_params.top_p

    question = to_glm_message(messages)

    stream_response = glm_stream_complete(api_key, model_name, question, temperature, top_p)
    return stream_response
