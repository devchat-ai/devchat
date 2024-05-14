from typing import Tuple

import pytest

from devchat.openai import OpenAIChat, OpenAIChatConfig
from devchat.store import Store


@pytest.fixture(name="chat_store", scope="function")
def create_chat_store(tmp_path) -> Tuple[OpenAIChat, Store]:
    config = OpenAIChatConfig(model="gpt-3.5-turbo")
    chat = OpenAIChat(config)
    return chat, Store(tmp_path, chat)


def _create_response_str(cmpl_id: str, created: int, content: str) -> str:
    """Create a response string from the given parameters."""
    return f"""
    {{
      "id": "{cmpl_id}",
      "object": "chat.completion",
      "created": {created},
      "model": "gpt-3.5-turbo-0301",
      "usage": {{"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87}},
      "choices": [
        {{
          "message": {{
            "role": "assistant",
            "content": "{content}"
          }},
          "finish_reason": "stop",
          "index": 0
        }}
      ]
    }}
    """


def test_get_prompt(chat_store):
    chat, store = chat_store
    prompt = chat.init_prompt("Where was the 2020 World Series played?")
    response_str = _create_response_str(
        "chatcmpl-6p9XYPYSTTRi0xEviKjjilqrWU2Ve",
        1577649420,
        "The 2020 World Series was played in Arlington, Texas.",
    )
    prompt.set_response(response_str)
    store.store_prompt(prompt)

    assert store.get_prompt(prompt.hash).timestamp == prompt.timestamp


def test_select_recent(chat_store):
    chat, store = chat_store

    # Create and store 5 prompts
    hashes = []
    for index in range(5):
        prompt = chat.init_prompt(f"Question {index}")
        response_str = _create_response_str(
            f"chatcmpl-id{index}", 1577649420 + index, f"Answer {index}"
        )
        prompt.set_response(response_str)
        store.store_prompt(prompt)
        hashes.append(prompt.hash)

    # Test selecting recent prompts
    # Get prompts from differnt topic is unexpected
    # it will return the prompts from the same topic
    recent_prompts = store.select_prompts(0, 3)
    assert len(recent_prompts) == 1
    for index, prompt in enumerate(recent_prompts):
        assert prompt.hash == hashes[4 - index]


def test_select_topics_no_topics(chat_store):
    _, store = chat_store

    # Test selecting topics when there are no topics
    topics = store.select_topics(0, 5)
    assert len(topics) == 0


def test_select_recent_with_topic_tree(chat_store):
    chat, store = chat_store

    # Create and store a root prompt
    root_prompt = chat.init_prompt("Root question")
    root_response_str = _create_response_str("chatcmpl-root", 1677649400, "Root answer")
    root_prompt.set_response(root_response_str)
    store.store_prompt(root_prompt)

    # Create and store a child prompt for the root prompt
    child_prompt = chat.init_prompt("Child question")
    child_prompt.parent = root_prompt.hash
    child_response_str = _create_response_str("chatcmpl-child", 1677649401, "Child answer")
    child_prompt.set_response(child_response_str)
    store.store_prompt(child_prompt)

    # Create and store 1 grandchild prompts for the child prompt
    grandchild_hashes = []
    for index in range(1):
        grandchild_prompt = chat.init_prompt(f"Grandchild question {index}")
        grandchild_prompt.parent = child_prompt.hash
        response_str = _create_response_str(
            f"chatcmpl-grandchild{index}", 1677649402 + index, f"Grandchild answer {index}"
        )
        grandchild_prompt.set_response(response_str)
        store.store_prompt(grandchild_prompt)
        grandchild_hashes.append(grandchild_prompt.hash)

    # Test selecting topics
    topics = store.select_topics(0, 5)
    assert len(topics) == 1
    assert topics[0]["root_prompt"]["hash"] == root_prompt.hash

    # Test selecting recent prompts within the nested topic
    recent_prompts = store.select_prompts(1, 3, topic=root_prompt.hash)
    assert len(recent_prompts) == 2
    assert recent_prompts[0].hash == child_prompt.hash
    assert recent_prompts[1].hash == root_prompt.hash


@pytest.fixture(name="prompt_tree", scope="function")
def create_prompt_tree(chat_store):
    chat, store = chat_store

    # Create and store a root prompt
    root_prompt = chat.init_prompt("Root question")
    root_response_str = _create_response_str("chatcmpl-root", 1677649400, "Root answer")
    root_prompt.set_response(root_response_str)
    store.store_prompt(root_prompt)

    # Create and store a child prompt for the root prompt
    child_prompt = chat.init_prompt("Child question")
    child_prompt.parent = root_prompt.hash
    child_response_str = _create_response_str("chatcmpl-child", 1677649400 + 1, "Child answer")
    child_prompt.set_response(child_response_str)
    store.store_prompt(child_prompt)

    # Create and store a grandchild prompt for the child prompt
    grandchild_prompt = chat.init_prompt("Grandchild question")
    grandchild_prompt.parent = child_prompt.hash
    grandchild_response_str = _create_response_str(
        "chatcmpl-grandchild", 1677649400 + 2, "Grandchild answer"
    )
    grandchild_prompt.set_response(grandchild_response_str)
    store.store_prompt(grandchild_prompt)

    # Create and store another root prompt
    other_root_prompt = chat.init_prompt("Other root question")
    other_root_response_str = _create_response_str(
        "chatcmpl-other-root", 1677649400 + 3, "Other root answer"
    )
    other_root_prompt.set_response(other_root_response_str)
    store.store_prompt(other_root_prompt)

    return store, root_prompt, child_prompt, grandchild_prompt, other_root_prompt


def test_delete_prompt_child(prompt_tree):
    store, _, child_prompt, _, _ = prompt_tree

    # Test deleting the child prompt
    assert not store.delete_prompt(child_prompt.hash)


def test_delete_prompt_grandchild(prompt_tree):
    store, root_prompt, _, grandchild_prompt, other_root_prompt = prompt_tree

    # Test deleting the grandchild prompt
    assert store.delete_prompt(grandchild_prompt.hash)

    # Verify the trees after deletion
    topics = store.select_topics(0, 5)
    assert len(topics) == 2
    assert topics[0]["root_prompt"]["hash"] == other_root_prompt.hash
    assert topics[1]["root_prompt"]["hash"] == root_prompt.hash


def test_delete_prompt_other_root(prompt_tree):
    store, root_prompt, _, _, other_root_prompt = prompt_tree

    # Test deleting the other root prompt
    assert store.delete_prompt(other_root_prompt.hash)

    # Verify the trees after deletion
    topics = store.select_topics(0, 5)
    assert len(topics) == 1
    assert topics[0]["root_prompt"]["hash"] == root_prompt.hash
