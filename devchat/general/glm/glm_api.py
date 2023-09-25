import time
import json
import zhipuai


def call_zhipu(api_key, model_name, messages, temperature, top_p):
    zhipuai.api_key = api_key
    response = zhipuai.model_api.sse_invoke(
        model=model_name,
        prompt=messages,
        temperature=temperature,
        top_p=top_p,
        incremental=True
    )
    return response


class StreamIterWrapper:
    def __init__(self, responses, model_name):
        self.events = responses.events()
        self.create_time = int(time.time())
        self.model_name = model_name

    def __iter__(self):
        return self

    def __aiter__(self):
        return self

    def __next__(self):
        try:
            stream_response = {
                'id': f'glm_{self.create_time}',
                'created': self.create_time,
                'object': 'chat.completion.chunk',
                'model': self.model_name,
                'choices': [
                    {
                        'index': 0,
                        'finish_reason': 'stop',
                        'delta': {
                            'role': 'assistant',
                            'content': ''
                        }
                    }
                ],
                'usage': {
                    'prompt_tokens': 0,
                    'completion_tokens': 0
                }
            }

            event = next(self.events)

            if event.event == "add":
                stream_response['choices'][0]['delta']['content'] = event.data
            elif event.event in ["error", "interrupted"]:
                stream_response['choices'][0]['delta']['content'] = event.data
                stream_response['choices'][0]['delta']['finish_reason'] = event.event
            elif event.event == "finish":
                meta = json.loads(event.meta)
                stream_response['choices'][0]['delta']['content'] = event.data
                stream_response['usage']['completion_tokens'] = meta['usage']['total_tokens']
            else:
                stream_response['choices'][0]['delta']['content'] = event.data
            return stream_response
        except StopIteration as exc:  # If there is no more event
            raise StopIteration from exc


def complete(api_key, model_name, messages, temperature, top_p):
    response = call_zhipu(api_key, model_name, messages, temperature, top_p)

    responses = {
        "id": "",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": ""
                }
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
    }

    for event in response.events():
        if event.event == "add":
            responses['choices'][0]['message']['content'] += event.data
        elif event.event in ["error", "interrupted"]:
            responses['choices'][0]['message']['content'] += event.data
            responses['choices'][0]['message']['finish_reason'] = event.event
        elif event.event == "finish":
            meta = json.loads(event.meta)
            responses['choices'][0]['message']['content'] += event.data
            responses['usage']['completion_tokens'] = meta['usage']['total_tokens']
            responses['id'] = meta['task_id']
        else:
            responses['choices'][0]['message']['content'] += event.data
    return responses

def stream_complete(api_key, model_name, messages, temperature, top_p):
    response = call_zhipu(api_key, model_name, messages, temperature, top_p)
    stream_iterator = StreamIterWrapper(response, model_name)
    return stream_iterator
