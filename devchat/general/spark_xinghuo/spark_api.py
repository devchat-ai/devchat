import _thread as thread
import base64
import datetime
import hashlib
import time
import hmac
import json
import queue
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websocket
answer = ""

create_time = int(time.time())

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = self.Spark_url + '?' + urlencode(v)
        return url


def on_error(ws, error):
    print("### error:", error)


def on_close(ws,one,two):
    print(" ")


def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain= ws.domain,question=ws.question, user_id=ws.user_id, temperature=ws.temperature, max_tokens=ws.max_tokens))
    ws.send(data)


def gen_params(appid, domain,question, user_id, temperature, max_tokens):
    """
    通过appid和用户的提问来生成请参数
    """
    data = {
        "header": {
            "app_id": appid,
            "uid": user_id
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "random_threshold": temperature,
                "max_tokens": max_tokens,
                "auditing": "default",
                "temperature": temperature
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


class SparkApi:
    def __init__(self, appid, api_key, api_secret, Spark_url, domain, question, user_id="1234", temperature=0.5, max_tokens=4000):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.Spark_url = Spark_url
        self.domain = domain
        self.question = question
        self.user_id = user_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.error = False
        self.wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)
        self.wsUrl = self.wsParam.create_url()
        self.data_queue = queue.Queue()

    def on_message(self, ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            self.error = True
            ws.close()
        else:
            choices = data["payload"]["choices"]
            stream_response = {
                'id': data['header']['sid'],
                'created': create_time,
                'object': 'chat.completion.chunk',
                'model': 'xinghuo-2',
                'choices': [
                    {
                        'index': 0,
                        'finish_reason': 'stop' if choices["status"] == 2 else 'null',
                        'delta': {'role': 'assistant', 'content': choices["text"][0]["content"]}
                    }
                ],
                'usage': {
                    'prompt_tokens': 0 if 'usage' not in data else data['usage']['text']['prompt_tokens'],
                    'completion_tokens': 0 if 'usage' not in data else data['usage']['text']['completion_tokens']
                }
            }
            
            self.data_queue.put(stream_response)
            if choices["status"] == 2:
                ws.close()

    def run(self):
        ws = websocket.WebSocketApp(self.wsUrl, on_message=self.on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        ws.appid = self.appid
        ws.question = self.question
        ws.domain = self.domain
        ws.user_id = self.user_id
        ws.temperature = self.temperature
        ws.max_tokens = self.max_tokens
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    
    def run_nostream(self):
        ws = websocket.WebSocketApp(self.wsUrl, on_message=self.on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        ws.appid = self.appid
        ws.question = self.question
        ws.domain = self.domain
        ws.user_id = self.user_id
        ws.temperature = self.temperature
        ws.max_tokens = self.max_tokens
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        responses = {}
        for response in self.get_responses():
            responses['id'] = response['id']
            responses['object'] = 'chat.completion.chunk'
            responses['created'] = response['created']
            responses['model'] = response['model']
            if 'choices' not in responses:
                responses['choices'] = [
                    {
                        'index': response['choices'][0]['index'],
                        'finish_reason': response['choices'][0]['finish_reason'],
                        'message': { 'role': 'assistant', 'content': ''}
                    }
                ]
            responses['choices'][0]['message']['content'] += response['choices'][0]['delta']['content']
        
            if 'usage' not in responses:
                responses['usage'] = {
                    'prompt_tokens': 0,
                    'completion_tokens': 0
                }
            responses['usage']['prompt_tokens'] += response['usage']['prompt_tokens']
            responses['usage']['completion_tokens'] += response['usage']['completion_tokens']
            
        return responses

    def get_responses(self):
        while True and not self.error:
            response = self.data_queue.get()
            if response and response['choices'][0]['finish_reason'] == 'stop':
                yield response
                break
            else:
                yield response