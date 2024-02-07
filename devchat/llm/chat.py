import json
import os
import sys
from functools import wraps

import openai

from .memory.base import ChatMemory
from .openai import (
    chat_completion_no_stream_return_json,
    chat_completion_stream,
    chat_completion_stream_commit,
    chunks_content,
    retry_timeout,
    stream_out_chunk,
    to_dict_content_and_call,
)
from .pipeline import exception_handle, pipeline, retry

chat_completion_stream_out = exception_handle(
    retry(
        pipeline(
            chat_completion_stream_commit,
            retry_timeout,
            stream_out_chunk,
            chunks_content,
            to_dict_content_and_call,
        ),
        times=3,
    ),
    lambda err: {
        "content": None,
        "function_name": None,
        "parameters": "",
        "error": err.type if isinstance(err, openai.APIError) else err,
    },
)


def chat(
    prompt,
    memory: ChatMemory = None,
    stream_out: bool = False,
    model: str = os.environ.get("LLM_MODEL", "gpt-3.5-turbo-1106"),
    **llm_config,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal prompt, memory, model, llm_config
            prompt = prompt.format(**kwargs)
            messages = memory.contexts() if memory else []
            if not any(item["content"] == prompt for item in messages) and prompt:
                messages.append({"role": "user", "content": prompt})
            if "__user_request__" in kwargs:
                messages.append(kwargs["__user_request__"])
                del kwargs["__user_request__"]

            llm_config["model"] = model
            if not stream_out:
                response = chat_completion_stream(messages, llm_config=llm_config)
            else:
                response = chat_completion_stream_out(messages, llm_config=llm_config)
            if not response.get("content", None):
                print(f"call {func.__name__} failed:", response["error"], file=sys.stderr)
                return None

            if memory:
                memory.append(
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response["content"]},
                )
            return response["content"]

        return wrapper

    return decorator


def chat_json(
    prompt,
    memory: ChatMemory = None,
    model: str = os.environ.get("LLM_MODEL", "gpt-3.5-turbo-1106"),
    **llm_config,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal prompt, memory, model, llm_config
            prompt = prompt.format(**kwargs)
            messages = memory.contexts() if memory else []
            if not any(item["content"] == prompt for item in messages):
                messages.append({"role": "user", "content": prompt})

            llm_config["model"] = model
            response = chat_completion_no_stream_return_json(messages, llm_config=llm_config)
            if not response:
                print(f"call {func.__name__} failed.", file=sys.stderr)

            if memory:
                memory.append(
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": json.dumps(response)},
                )
            return response

        return wrapper

    return decorator
