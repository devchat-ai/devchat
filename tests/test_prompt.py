import json
import os
import pytest
from devchat.message import Message
from devchat.prompt import Prompt


def test_prompt_init_and_set_response():
    prompt = Prompt(model="gpt-3.5-turbo")
    assert prompt.model == "gpt-3.5-turbo"

    response_str = '''
    {
      "id": "chatcmpl-6p9XYPYSTTRi0xEviKjjilqrWU2Ve",
      "object": "chat.completion",
      "created": 1677649420,
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

    assert prompt.response_meta == {
        'id': 'chatcmpl-6p9XYPYSTTRi0xEviKjjilqrWU2Ve',
        'object': 'chat.completion'
    }
    assert prompt.response_time == 1677649420
    assert prompt.request_tokens == 56
    assert prompt.response_tokens == 31
    assert len(prompt.responses) == 1
    assert prompt.responses[0].role == "assistant"
    assert prompt.responses[0].content == "The 2020 World Series was played in Arlington, Texas."


def test_prompt_model_mismatch():
    prompt = Prompt(model="gpt-3.5-turbo")

    response_str = '''
    {
      "choices": [
        {
          "finish_reason": "stop",
          "index": 0,
          "message": {
            "content": "\\n\\n1, 2, 3, 4, 5, 6, 7, 8, 9, 10.",
            "role": "assistant"
          }
        }
      ],
      "created": 1677825456,
      "id": "chatcmpl-6ptKqrhgRoVchm58Bby0UvJzq2ZuQ",
      "model": "gpt-4",
      "object": "chat.completion",
      "usage": {
        "completion_tokens": 301,
        "prompt_tokens": 36,
        "total_tokens": 337
      }
    }
    '''
    with pytest.raises(ValueError):
        prompt.set_response(response_str)


@pytest.fixture(scope="module")
def stream_responses():
    current_dir = os.path.dirname(__file__)
    folder_path = os.path.join(current_dir, "stream_responses")
    responses = []

    file_names = os.listdir(folder_path)
    sorted_file_names = sorted(file_names, key=lambda x: int(x.split('.')[0][8:]))

    for file_name in sorted_file_names:
        with open(os.path.join(folder_path, file_name), 'r') as file:
            response = json.load(file)
            responses.append(response)

    return responses


def test_append_response(stream_responses):
    prompt = Prompt("gpt-3.5-turbo-0301")

    for response in stream_responses:
        prompt.append_response(json.dumps(response))

    expected_messages = [
        Message(role='assistant', content='Tomorrow.'),
        Message(role='assistant', content='Tomorrow!')
    ]

    assert len(prompt.responses) == len(expected_messages)
    for index, message in prompt.responses.items():
        assert message.role == expected_messages[index].role
        assert message.content == expected_messages[index].content
