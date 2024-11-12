"""
openai api utils
"""

# flake8: noqa: E402
# Import necessary libraries
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import httpx
import openai
import oyaml as yaml

from devchat.ide import IDEService
from devchat.workflow.path import CHAT_CONFIG_FILENAME, CHAT_DIR

from .pipeline import (
    RetryException,  # Import RetryException class
    exception_handle,  # Function to handle exceptions
    parallel,  # Function to run tasks in parallel
    pipeline,  # Function to create a pipeline of tasks
    retry,  # Function to retry a task
)


def _try_remove_markdown_block_flag(content):
    """
    If the content is a markdown block, this function removes the header ```xxx and footer ```
    """
    # Define a regex pattern to match the header and footer of a markdown block
    pattern = r"^\s*```\s*(\w+)\s*\n(.*?)\n\s*```\s*$"

    # Use the re module to match the pattern
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

    if match:
        # If a match is found, extract the content of the markdown block and return it
        _ = match.group(1)  # language
        markdown_content = match.group(2)
        return markdown_content.strip()
    # If no match is found, return the original content
    return content


# 模块级变量用于缓存配置
_chat_config: Dict[str, Any] = {}


def _load_chat_config() -> None:
    """加载聊天配置到全局变量"""
    global _chat_config
    chat_config_path = Path(CHAT_DIR) / CHAT_CONFIG_FILENAME
    with open(chat_config_path, "r", encoding="utf-8") as file:
        _chat_config = yaml.safe_load(file)


def get_maxtokens_by_model(model: str) -> int:
    # 如果配置还没有加载，则加载配置
    if not _chat_config:
        _load_chat_config()

    # 默认值设置为1024
    default_max_tokens = 1024

    # 检查模型是否在配置中
    if model in _chat_config.get("models", {}):
        # 如果模型存在，尝试获取max_tokens，如果不存在则返回默认值
        return _chat_config["models"][model].get("max_tokens", default_max_tokens)
    else:
        # 如果模型不在配置中，返回默认值
        return default_max_tokens


def chat_completion_stream_commit(
    messages: List[Dict],  # [{"role": "user", "content": "hello"}]
    llm_config: Dict,  # {"model": "...", ...}
):
    """
    This function is used to commit chat completion stream
    """
    proxy_url = os.environ.get("DEVCHAT_PROXY", "")
    proxy_setting = {"proxy": {"https://": proxy_url, "http://": proxy_url}} if proxy_url else {}

    # Initialize OpenAI client with API key, base URL and http client
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", None),
        base_url=os.environ.get("OPENAI_API_BASE", None),
        http_client=httpx.Client(**proxy_setting, trust_env=False),
    )

    # Update llm_config dictionary
    llm_config["stream"] = True
    llm_config["timeout"] = 60
    llm_config["max_tokens"] = get_maxtokens_by_model(llm_config["model"])
    # Return chat completions
    return client.chat.completions.create(messages=messages, **llm_config)


def chat_completion_stream_raw(**kwargs):
    """
    This function is used to get raw chat completion stream
    """
    proxy_url = os.environ.get("DEVCHAT_PROXY", "")
    proxy_setting = {"proxy": {"https://": proxy_url, "http://": proxy_url}} if proxy_url else {}

    # Initialize OpenAI client with API key, base URL and http client
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", None),
        base_url=os.environ.get("OPENAI_API_BASE", None),
        http_client=httpx.Client(**proxy_setting, trust_env=False),
    )

    # Update kwargs dictionary
    kwargs["stream"] = True
    kwargs["timeout"] = 60
    kwargs["max_tokens"] = get_maxtokens_by_model(kwargs["model"])
    # Return chat completions
    return client.chat.completions.create(**kwargs)


def stream_out_chunk(chunks):
    """
    This function is used to print out chunks of data
    """
    for chunk in chunks:
        chunk_dict = chunk.dict()
        if len(chunk_dict["choices"]) > 0:
            delta = chunk_dict["choices"][0]["delta"]
            if delta.get("content", None):
                print(delta["content"], end="", flush=True)
            yield chunk


def retry_timeout(chunks):
    """
    This function is used to handle timeout errors
    """
    try:
        for chunk in chunks:
            yield chunk
    except (openai.APIConnectionError, openai.APITimeoutError) as err:
        IDEService().ide_logging("info", f"in retry_timeout: err: {err}")
        raise RetryException(err) from err


def chunk_list(chunks):
    """
    This function is used to convert chunks into a list
    """
    return [chunk for chunk in chunks]


def chunks_content(chunks):
    """
    This function is used to extract content from chunks
    """
    content = None
    for chunk in chunks:
        chunk_dict = chunk.dict()
        if len(chunk_dict["choices"]) > 0:
            delta = chunk_dict["choices"][0]["delta"]
            if delta.get("content", None):
                if content is None:
                    content = ""
                content += delta["content"]
    return content


def chunks_call(chunks):
    """
    This function is used to extract tool
    calls from chunks
    """
    tool_calls = []

    for chunk in chunks:
        chunk = chunk.dict()
        if len(chunk["choices"]) > 0:
            delta = chunk["choices"][0]["delta"]
            if "tool_calls" in delta and delta["tool_calls"]:
                tool_call = delta["tool_calls"][0]["function"]
                if delta["tool_calls"][0].get("index", None) is not None:
                    index = delta["tool_calls"][0]["index"]
                    if index >= len(tool_calls):
                        tool_calls.append({"name": None, "arguments": ""})
                if tool_call.get("name", None):
                    tool_calls[-1]["name"] = tool_call["name"]
                if tool_call.get("arguments", None):
                    tool_calls[-1]["arguments"] += tool_call["arguments"]
    return tool_calls


def content_to_json(content):
    """
    This function is used to convert content to JSON
    """
    try:
        content_no_block = _try_remove_markdown_block_flag(content)
        response_obj = json.loads(content_no_block, strict=False)
        return response_obj
    except json.JSONDecodeError as err:
        IDEService().ide_logging("debug", f"Receive content: {content}")
        IDEService().ide_logging("debug", f"in content_to_json: json decode error: {err}")
        raise RetryException(err) from err
    except Exception as err:
        IDEService().ide_logging("debug", f"in content_to_json: other error: {err}")
        raise err


def to_dict_content_and_call(content, tool_calls=None):
    """
    This function is used to convert content and tool calls to a dictionary
    """
    if tool_calls is None:
        tool_calls = []
    return {
        "content": content,
        "function_name": tool_calls[0]["name"] if tool_calls else None,
        "parameters": tool_calls[0]["arguments"] if tool_calls else "",
        "tool_calls": tool_calls,
    }


# Define a pipeline function for chat completion content.
# This pipeline first commits a chat completion stream, handles any timeout errors,
# and then extracts the content from the chunks.
# If any step in the pipeline fails, it will retry the entire pipeline up to 3 times.
chat_completion_content = retry(
    pipeline(chat_completion_stream_commit, retry_timeout, chunks_content), times=3
)

# Define a pipeline function for chat completion stream content.
# This pipeline first commits a chat completion stream, handles any timeout errors,
# streams out the chunk, and then extracts the content from the chunks.
# If any step in the pipeline fails, it will retry the entire pipeline up to 3 times.
chat_completion_stream_content = retry(
    pipeline(chat_completion_stream_commit, retry_timeout, stream_out_chunk, chunks_content),
    times=3,
)

# Define a pipeline function for chat completion call.
# This pipeline first commits a chat completion stream, handles any timeout errors,
#  and then extracts the tool calls from the chunks.
# If any step in the pipeline fails, it will retry the entire pipeline up to 3 times.
chat_completion_call = retry(
    pipeline(chat_completion_stream_commit, retry_timeout, chunks_call), times=3
)

# Define a pipeline function for chat completion without streaming and return a JSON object.
# This pipeline first commits a chat completion stream, handles any timeout errors, extracts
#  the content from the chunks and then converts the content to JSON.
# If any step in the pipeline fails, it will retry the entire pipeline up to 3 times.
# If a JSONDecodeError is encountered during the content to JSON conversion, it will log the
#  error and retry the pipeline.
# If any other exception is encountered, it will log the error and raise it.
chat_completion_no_stream_return_json_with_retry = exception_handle(
    retry(
        pipeline(chat_completion_stream_commit, retry_timeout, chunks_content, content_to_json),
        times=3,
    ),
    None,
)


def chat_completion_no_stream_return_json(messages: List[Dict], llm_config: Dict):
    """
    This function is used to get chat completion without streaming and return JSON object
    """
    llm_config["response_format"] = {"type": "json_object"}
    return chat_completion_no_stream_return_json_with_retry(
        messages=messages, llm_config=llm_config
    )


# Define a pipeline function for chat completion stream.
# This pipeline first commits a chat completion stream, handles any timeout errors,
#  extracts the content from the chunks, and then converts the content and tool calls
#  to a dictionary.
# If any step in the pipeline fails, it will retry the entire pipeline up to 3 times.
# If an exception is encountered, it will return a dictionary with None values and the error.
chat_completion_stream = exception_handle(
    retry(
        pipeline(
            chat_completion_stream_commit,
            retry_timeout,
            chunks_content,
            to_dict_content_and_call,
        ),
        times=3,
    ),
    None,
)

# Define a pipeline function for chat call completion stream.
# This pipeline first commits a chat completion stream, handles any timeout errors,
#  converts the chunks to a list, extracts the content and tool calls from the chunks
#  in parallel, and then converts the content and tool calls to a dictionary.
# If any step in the pipeline fails, it will retry the entire pipeline up to 3 times.
# If an exception is encountered, it will return a dictionary with None values, an empty
#  tool calls list, and the error.
chat_call_completion_stream = exception_handle(
    retry(
        pipeline(
            chat_completion_stream_commit,
            retry_timeout,
            chunk_list,
            parallel(chunks_content, chunks_call),
            to_dict_content_and_call,
        ),
        times=3,
    ),
    None,
)
