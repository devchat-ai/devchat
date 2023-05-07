import json
import os
import pytest
from devchat.message import MessageType
from devchat.openai import OpenAIMessage
from devchat.openai import OpenAIPrompt
from devchat.utils import get_git_user_info


def test_prompt_init_and_set_response():
    name, email = get_git_user_info()
    prompt = OpenAIPrompt(model="gpt-3.5-turbo", user_name=name, user_email=email)
    assert prompt.model == "gpt-3.5-turbo"

    prompt.set_request("Where was the 2020 World Series played?")
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

    assert prompt.timestamp == 1677649420
    assert prompt.request_tokens == 56
    assert prompt.response_tokens == 31
    assert len(prompt.response) == 1
    assert prompt.response[0].role == "assistant"
    assert prompt.response[0].content == "The 2020 World Series was played in Arlington, Texas."


def test_prompt_model_mismatch():
    name, email = get_git_user_info()
    prompt = OpenAIPrompt(model="gpt-3.5-turbo", user_name=name, user_email=email)

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


@pytest.fixture(scope="module", name='responses')
def fixture_responses():
    current_dir = os.path.dirname(__file__)
    folder_path = os.path.join(current_dir, "stream_responses")
    stream_responses = []

    file_names = os.listdir(folder_path)
    sorted_file_names = sorted(file_names, key=lambda x: int(x.split('.')[0][8:]))

    for file_name in sorted_file_names:
        with open(os.path.join(folder_path, file_name), 'r', encoding='utf-8') as file:
            response = json.load(file)
            stream_responses.append(response)

    return stream_responses


def test_append_response(responses):
    name, email = get_git_user_info()
    prompt = OpenAIPrompt("gpt-3.5-turbo-0301", name, email)

    for response in responses:
        prompt.append_response(json.dumps(response))

    expected_messages = [
        OpenAIMessage(role='assistant', content='Tomorrow.'),
        OpenAIMessage(role='assistant', content='Tomorrow!')
    ]

    assert len(prompt.response) == len(expected_messages)
    for index, message in prompt.response.items():
        assert message.role == expected_messages[index].role
        assert message.content == expected_messages[index].content


def test_messages_empty():
    prompt = OpenAIPrompt("davinci-codex", "John Doe", "john.doe@example.com")
    assert prompt.messages == []


def test_messages_instruct():
    prompt = OpenAIPrompt("davinci-codex", "John Doe", "john.doe@example.com")
    instruct_message = OpenAIMessage('Instructions', 'system')
    prompt.append_new(MessageType.INSTRUCT, 'Instructions')
    assert prompt.messages == [instruct_message.to_dict()]


def test_messages_context():
    prompt = OpenAIPrompt("davinci-codex", "John Doe", "john.doe@example.com")
    context_message = OpenAIMessage('Context', 'system')
    prompt.append_new(MessageType.CONTEXT, 'Context')
    expected_message = context_message.to_dict()
    expected_message["content"] = "<context>\n" + context_message.content + "\n</context>"
    assert prompt.messages == [expected_message]


def test_messages_record():
    prompt = OpenAIPrompt("davinci-codex", "John Doe", "john.doe@example.com")
    with pytest.raises(ValueError):
        prompt.append_new(MessageType.CHAT, 'Record')


def test_messages_request():
    prompt = OpenAIPrompt("davinci-codex", "John Doe", "john.doe@example.com")
    request_message = OpenAIMessage('Request', 'user')
    prompt.set_request('Request')
    expected_message = request_message.to_dict()
    assert prompt.messages == [expected_message]


def test_messages_combined():
    prompt = OpenAIPrompt("davinci-codex", "John Doe", "john.doe@example.com")
    instruct_message = OpenAIMessage('Instructions', 'system')
    context_message = OpenAIMessage('Context', 'system')
    request_message = OpenAIMessage('Request', 'user')

    prompt.append_new(MessageType.INSTRUCT, 'Instructions')
    prompt.append_new(MessageType.CONTEXT, 'Context')
    prompt.set_request('Request')

    expected_context_message = context_message.to_dict()
    expected_context_message["content"] = "<context>\n" + context_message.content + "\n</context>"

    expected_request_message = request_message.to_dict()
    expected_request_message["content"] = request_message.content

    assert prompt.messages == [
        instruct_message.to_dict(),
        expected_context_message,
        expected_request_message
    ]


def test_messages_invalid_append():
    prompt = OpenAIPrompt("davinci-codex", "John Doe", "john.doe@example.com")
    with pytest.raises(ValueError):
        prompt.append_new('invalid', 'Instructions')


def test_messages_invalid_request():
    prompt = OpenAIPrompt("davinci-codex", "John Doe", "john.doe@example.com")
    with pytest.raises(ValueError):
        prompt.set_request("")
