# flake8: noqa: E402
import json
import os
import re
from typing import Dict, List

import httpx
import openai

from devchat.ide import IDEService

from .pipeline import (
    RetryException,
    exception_handle,
    exception_output_handle,
    parallel,
    pipeline,
    retry,
)


def _try_remove_markdown_block_flag(content):
    """
    如果content是一个markdown块，则删除它的头部```xxx和尾部```
    """
    # 定义正则表达式模式，用于匹配markdown块的头部和尾部
    pattern = r"^\s*```\s*(\w+)\s*\n(.*?)\n\s*```\s*$"

    # 使用re模块进行匹配
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

    if match:
        # 如果匹配成功，则提取出markdown块的内容并返回
        _ = match.group(1)  # language
        markdown_content = match.group(2)
        return markdown_content.strip()
    # 如果匹配失败，则返回原始内容
    return content


def chat_completion_stream_commit(
    messages: List[Dict],  # [{"role": "user", "content": "hello"}]
    llm_config: Dict,  # {"model": "...", ...}
):
    proxy_url = os.environ.get("DEVCHAT_PROXY", "")
    proxy_setting = {"proxy": {"https://": proxy_url, "http://": proxy_url}} if proxy_url else {}

    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", None),
        base_url=os.environ.get("OPENAI_API_BASE", None),
        http_client=httpx.Client(**proxy_setting, trust_env=False),
    )

    llm_config["stream"] = True
    llm_config["timeout"] = 60
    return client.chat.completions.create(messages=messages, **llm_config)


def chat_completion_stream_raw(**kwargs):
    proxy_url = os.environ.get("DEVCHAT_PROXY", "")
    proxy_setting = {"proxy": {"https://": proxy_url, "http://": proxy_url}} if proxy_url else {}

    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", None),
        base_url=os.environ.get("OPENAI_API_BASE", None),
        http_client=httpx.Client(**proxy_setting, trust_env=False),
    )

    kwargs["stream"] = True
    kwargs["timeout"] = 60
    return client.chat.completions.create(**kwargs)


def stream_out_chunk(chunks):
    for chunk in chunks:
        chunk_dict = chunk.dict()
        if len(chunk_dict["choices"]) > 0:
            delta = chunk_dict["choices"][0]["delta"]
            if delta.get("content", None):
                print(delta["content"], end="", flush=True)
            yield chunk


def retry_timeout(chunks):
    try:
        for chunk in chunks:
            yield chunk
    except (openai.APIConnectionError, openai.APITimeoutError) as err:
        IDEService().ide_logging("info", f"in retry_timeout: err: {err}")
        raise RetryException(err) from err


def chunk_list(chunks):
    return [chunk for chunk in chunks]


def chunks_content(chunks):
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
    try:
        content_no_block = _try_remove_markdown_block_flag(content)
        response_obj = json.loads(content_no_block)
        return response_obj
    except json.JSONDecodeError as err:
        IDEService().ide_logging("info", f"in content_to_json: json decode error: {err}")
        raise RetryException(err) from err
    except Exception as err:
        IDEService().ide_logging("info", f"in content_to_json: other error: {err}")
        raise err


def to_dict_content_and_call(content, tool_calls=None):
    if tool_calls is None:
        tool_calls = []
    return {
        "content": content,
        "function_name": tool_calls[0]["name"] if tool_calls else None,
        "parameters": tool_calls[0]["arguments"] if tool_calls else "",
        "tool_calls": tool_calls,
    }


chat_completion_content = retry(
    pipeline(chat_completion_stream_commit, retry_timeout, chunks_content), times=3
)

chat_completion_stream_content = retry(
    pipeline(chat_completion_stream_commit, retry_timeout, stream_out_chunk, chunks_content),
    times=3,
)

chat_completion_call = retry(
    pipeline(chat_completion_stream_commit, retry_timeout, chunks_call), times=3
)

chat_completion_no_stream_return_json_with_retry = exception_handle(
    retry(
        pipeline(chat_completion_stream_commit, retry_timeout, chunks_content, content_to_json),
        times=3,
    ),
    exception_output_handle(lambda err: None),
)


def chat_completion_no_stream_return_json(messages: List[Dict], llm_config: Dict):
    """call llm without stream, return json object"""
    llm_config["response_format"] = {"type": "json_object"}
    return chat_completion_no_stream_return_json_with_retry(
        messages=messages, llm_config=llm_config
    )


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
    lambda err: {"content": None, "function_name": None, "parameters": "", "error": err},
)

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
    lambda err: {
        "content": None,
        "function_name": None,
        "parameters": "",
        "tool_calls": [],
        "error": err,
    },
)
