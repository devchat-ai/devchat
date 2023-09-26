import time
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT


def message2prompt(messages):
    prompt = ""
    for message in messages:
        if "role" in message and message["role"] == "user":
            prompt += f"{HUMAN_PROMPT} {message['content']}"
    prompt += f"{AI_PROMPT}"
    return prompt


class StreamIterWrapper:
    def __init__(self, response):
        self.response = response
        self.create_time = int(time.time())

    def __iter__(self):
        return self

    def __aiter__(self):
        return self

    def __next__(self):
        try:
            completer = next(self.response)
            response_result = completer.dict()

            stream_response = {
                'id': f"anthropic-{self.create_time}",
                'created': self.create_time,
                'object': "chat.completion.chunk",
                'model': "claude-2",
                'choices': [
                    {
                        'index': 0,
                        'finish_reason': 'stop',
                        'delta': {
                            'role': 'assistant',
                            'content': response_result["completion"]
                        }
                    }
                ],
                'usage': {
                    'prompt_tokens': 0,
                    'completion_tokens': 0
                }
            }

            return stream_response
        except StopIteration as exc:  # If there is no more event
            raise StopIteration from exc


def complete(api_key, messages, temperature, max_tokens):
    anthropic = Anthropic(api_key = api_key)

    completion = anthropic.completions.create(
        model="claude-2",
        max_tokens_to_sample=max_tokens,
        prompt=message2prompt(messages),
        temperature=temperature
    )
    response_result = completion.dict()
    responses = {
        "id": f"anthropic-{response_result['log_id']}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "claude-2",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": response_result["completion"]
                }
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
    }

    return responses


def stream_complete(api_key, messages, temperature, max_tokens):
    anthropic = Anthropic(api_key = api_key)

    stream = anthropic.completions.create(
        model="claude-2",
        max_tokens_to_sample=max_tokens,
        stream=True,
        prompt=message2prompt(messages),
        temperature=temperature
    )

    return StreamIterWrapper(stream)
