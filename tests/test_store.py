from devchat.openai import OpenAIChatConfig, OpenAIChat
from devchat.store import Store


def test_get_prompt(tmp_path):
    config = OpenAIChatConfig(model="gpt-3.5-turbo")
    chat = OpenAIChat(config)
    store = Store(tmp_path / "store.graphml", chat)
    prompt = chat.init_prompt("Where was the 2020 World Series played?")
    response_str = '''
    {
      "id": "chatcmpl-6p9XYPYSTTRi0xEviKjjilqrWU2Ve",
      "object": "chat.completion",
      "created": 1577649420,
      "model": "gpt-3.5-turbo-0301",
      "usage": {"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87},
      "choices": [
        {
          "message": {
            "role": "assistant",
            "content": "The 2020 World Series was played in Arlington, Texas."
          },
          "finish_reason": "stop",
          "index": 0
        }
      ]
    }
    '''
    prompt.set_response(response_str)
    store.store_prompt(prompt)

    assert store.get_prompt(prompt.hash).timestamp == prompt.timestamp


def test_select_recent(tmp_path):
    config = OpenAIChatConfig(model="gpt-3.5-turbo")
    chat = OpenAIChat(config)
    store = Store(tmp_path / "store.graphml", chat)

    # Create and store 5 prompts
    hashes = []
    for index in range(5):
        prompt = chat.init_prompt(f"Question {index}")
        response_str = f'''
        {{
          "id": "chatcmpl-6p9XYPYSTTRi0xEviKjjilqrWU2Ve",
          "object": "chat.completion",
          "created": 167764942{index},
          "model": "gpt-3.5-turbo-0301",
          "usage": {{"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87}},
          "choices": [
            {{
              "message": {{
                "role": "assistant",
                "content": "Answer {index}"
              }},
              "finish_reason": "stop",
              "index": 0
            }}
          ]
        }}
        '''
        prompt.set_response(response_str)
        store.store_prompt(prompt)
        hashes.append(prompt.hash)

    # Test selecting recent prompts
    recent_prompts = store.select_prompts(0, 3)
    assert len(recent_prompts) == 3
    for index, prompt in enumerate(recent_prompts):
        assert prompt.hash == hashes[4 - index]


def test_select_topics_no_topics(tmp_path):
    config = OpenAIChatConfig(model="gpt-3.5-turbo")
    chat = OpenAIChat(config)
    store = Store(tmp_path / "store.graphml", chat)

    # Test selecting topics when there are no topics
    topics = store.select_topics(0, 5)
    assert len(topics) == 0


def test_select_topics_and_prompts_with_single_root(tmp_path):
    config = OpenAIChatConfig(model="gpt-3.5-turbo")
    chat = OpenAIChat(config)
    store = Store(tmp_path / "store.graphml", chat)

    # Create and store a root prompt
    root_prompt = chat.init_prompt("Root question")
    root_response_str = '''{
        "id": "chatcmpl-root",
        "object": "chat.completion",
        "created": 1677649400,
        "model": "gpt-3.5-turbo-0301",
        "usage": {"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87},
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Root answer"
                },
                "finish_reason": "stop",
                "index": 0
            }
        ]
    }'''
    root_prompt.set_response(root_response_str)
    store.store_prompt(root_prompt)

    # Create and store 3 child prompts for the root prompt
    child_hashes = []
    for index in range(3):
        child_prompt = chat.init_prompt(f"Child question {index}")
        child_prompt.parent = root_prompt.hash
        child_response_str = f'''{{
            "id": "chatcmpl-child{index}",
            "object": "chat.completion",
            "created": 167764940{index + 1},
            "model": "gpt-3.5-turbo-0301",
            "usage": {{"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87}},
            "choices": [
                {{
                    "message": {{
                        "role": "assistant",
                        "content": "Child answer {index}"
                    }},
                    "finish_reason": "stop",
                    "index": 0
                }}
            ]
        }}'''
        child_prompt.set_response(child_response_str)
        store.store_prompt(child_prompt)
        child_hashes.append(child_prompt.hash)

    # Test selecting topics
    topics = store.select_topics(0, 5)
    assert len(topics) == 1
    assert topics[0]['root_prompt'].hash == root_prompt.hash

    # Test selecting prompts within the topic
    recent_prompts = store.select_prompts(0, 2, topic=root_prompt.hash)
    assert len(recent_prompts) == 2
    for index, prompt in enumerate(recent_prompts):
        assert prompt.hash == child_hashes[2 - index]


def test_select_recent_with_topic_tree(tmp_path):
    config = OpenAIChatConfig(model="gpt-3.5-turbo")
    chat = OpenAIChat(config)
    store = Store(tmp_path / "store.graphml", chat)

    # Create and store a root prompt
    root_prompt = chat.init_prompt("Root question")
    root_response_str = '''{
        "id": "chatcmpl-root",
        "object": "chat.completion",
        "created": 1677649400,
        "model": "gpt-3.5-turbo-0301",
        "usage": {"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87},
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Root answer"
                },
                "finish_reason": "stop",
                "index": 0
            }
        ]
    }'''
    root_prompt.set_response(root_response_str)
    store.store_prompt(root_prompt)

    # Create and store a child prompt for the root prompt
    child_prompt = chat.init_prompt("Child question")
    child_prompt.parent = root_prompt.hash
    child_response_str = '''{
        "id": "chatcmpl-child",
        "object": "chat.completion",
        "created": 1677649401,
        "model": "gpt-3.5-turbo-0301",
        "usage": {"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87},
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Child answer"
                },
                "finish_reason": "stop",
                "index": 0
            }
        ]
    }'''
    child_prompt.set_response(child_response_str)
    store.store_prompt(child_prompt)

    # Create and store 2 grandchild prompts for the child prompt
    grandchild_hashes = []
    for index in range(2):
        grandchild_prompt = chat.init_prompt(f"Grandchild question {index}")
        grandchild_prompt.parent = child_prompt.hash
        grandchild_response_str = f'''{{
            "id": "chatcmpl-grandchild{index}",
            "object": "chat.completion",
            "created": 167764940{index + 2},
            "model": "gpt-3.5-turbo-0301",
            "usage": {{"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87}},
            "choices": [
                {{
                    "message": {{
                        "role": "assistant",
                        "content": "Grandchild answer {index}"
                    }},
                    "finish_reason": "stop",
                    "index": 0
                }}
            ]
        }}'''
        grandchild_prompt.set_response(grandchild_response_str)
        store.store_prompt(grandchild_prompt)
        grandchild_hashes.append(grandchild_prompt.hash)

    # Test selecting topics
    topics = store.select_topics(0, 5)
    assert len(topics) == 1
    assert topics[0]['root_prompt'].hash == root_prompt.hash

    # Test selecting recent prompts within the nested topic
    recent_prompts = store.select_prompts(1, 3, topic=root_prompt.hash)
    assert len(recent_prompts) == 2
    assert recent_prompts[0].hash == grandchild_hashes[0]
    assert recent_prompts[1].hash == child_prompt.hash
