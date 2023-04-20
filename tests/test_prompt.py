import pytest
from devchat.prompt import Prompt


def test_prompt_init_and_set_response():
    prompt = Prompt(model="gpt-3.5-turbo")
    assert prompt.model == "gpt-3.5-turbo"

    response_str = '''
    {
      "id": "chatcmpl-6p9XYPYSTTRi0xEviKjjilqrWU2Ve",
      "object": "chat.completion",
      "created": 1677649420,
      "model": "gpt-3.5-turbo",
      "usage": {"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87},
      "choices": [
        {
          "message": {
            "role": "assistant",
            "content": "The 2020 World Series was played in Arlington, Texas at the Globe Life Field, which was the new home stadium for the Texas Rangers."
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
    assert len(prompt.messages) == 1
    assert prompt.messages[0].role == "assistant"
    assert prompt.messages[0].content == "The 2020 World Series was played in Arlington, Texas at the Globe Life Field, which was the new home stadium for the Texas Rangers."

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
      "model": "gpt-3.5-turbo-0301",
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
