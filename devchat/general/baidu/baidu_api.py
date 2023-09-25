import json
import time
import requests


def get_access_token(api_key, api_secret):
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=" + \
          f"client_credentials&client_id={api_key}&client_secret={api_secret}"

    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
    return response.json().get("access_token")


class StreamIterWrapper:
    def __init__(self, response, model):
        self.iter_lines = response.iter_lines()
        self.create_time = int(time.time())
        self.model = model

    def __iter__(self):
        return self

    def __aiter__(self):
        return self

    def __next__(self):
        try:
            response_line = next(self.iter_lines)
            if response_line == b'':
                return self.__next__()

            response_line = response_line.replace(b'data: ', b'')
            response_result = json.loads(response_line.decode('utf-8'))
            stream_response = {
                'id': response_result["id"],
                'created': self.create_time,
                'object': response_result["object"],
                'model': self.model,
                'choices': [
                    {
                        'index': 0,
                        'finish_reason': 'stop',
                        'delta': {
                            'role': 'assistant',
                            'content': response_result["result"]
                        }
                    }
                ],
                'usage': {
                    'prompt_tokens': response_result["usage"]["prompt_tokens"],
                    'completion_tokens': response_result["usage"]["completion_tokens"]
                }
            }

            return stream_response
        except StopIteration as exc:  # If there is no more event
            raise StopIteration from exc


def complete(model, api_key, api_secret, messages, temperature):
    if model == "ERNIE-Bot":
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions" + \
               "?access_token=" + get_access_token(api_key, api_secret)
    elif model == "llama-2-13b-chat":
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/" + \
              "llama_2_13b?access_token=" + get_access_token(api_key, api_secret)
    else:
        raise ValueError("Model not supported")

    payload = json.dumps({
        "messages": messages,
        "temperature": temperature
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload, timeout=60)

    response_result = json.loads(response.text)
    responses = {
        "id": response_result["id"],
        "object": response_result["object"],
        "created": response_result["created"],
        "model": model,
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": response_result["result"]
                }
            }
        ],
        "usage": {
            "prompt_tokens": response_result["usage"]["prompt_tokens"],
            "completion_tokens": response_result["usage"]["completion_tokens"]
        }
    }
    return responses


def stream_complete(model, api_key, api_secret, messages, temperature):
    if model == "ERNIE-Bot":
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/" + \
            "completions?access_token=" + get_access_token(api_key, api_secret)
    elif model == "llama-2-13b-chat":
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/" + \
            "llama_2_13b?access_token=" + get_access_token(api_key, api_secret)
    else:
        raise ValueError("Model not supported")

    payload = json.dumps({
        "messages": messages,
        "temperature": temperature,
        "stream": True
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload, stream=True, timeout=60)
    return StreamIterWrapper(response, model)
