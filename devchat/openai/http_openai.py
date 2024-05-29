import http.client
import json
import os
import ssl
import sys
from urllib.parse import urlparse


class LineReader:
    def __init__(self, response):
        self.response = response

    def __iter__(self):
        return self

    def __next__(self):
        line = self.response.readline()
        if not line:
            raise StopIteration
        line = line.strip()
        if not line:
            return self.__next__()
        line = line.decode("utf-8")
        if not line.startswith("data:"):
            print("Receive invalid line: {line}", end="\n\n", file=sys.stderr)
            raise ValueError(f"Invalid line: {line}")

        if line[5:].strip() == "[DONE]":
            raise StopIteration
        try:
            return json.loads(line[5:])
        except json.JSONDecodeError as err:
            print(f"Error decoding JSON: {err}", end="\n\n", file=sys.stderr)
            raise ValueError(f"Invalid line: {line}") from err


def stream_response(connection: http.client.HTTPSConnection, data, headers):
    connection.request("POST", "/v1/chat/completions", body=json.dumps(data), headers=headers)
    response = connection.getresponse()

    if response.status != 200:
        print(
            f"Error: {response.status} - {response.reason} {response.read()}",
            end="\n\n",
            file=sys.stderr,
        )
        return None
    return LineReader(response=response)


def stream_request(api_key, api_base, data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    if api_base.startswith("https://"):
        url = api_base[8:]
    elif api_base.startswith("http://"):
        url = api_base[7:]
    else:
        print("Invalid API base URL", end="\n\n", file=sys.stderr)
        raise ValueError("Invalid API base URL")

    url = url.split("/")[0]
    proxy_url = os.environ.get("DEVCHAT_PROXY", "")
    parsed_url = urlparse(proxy_url)
    proxy_setting = {
        "host": parsed_url.hostname,
        **({"port": parsed_url.port} if parsed_url.port else {}),
    }

    if api_base.startswith("https://"):
        if proxy_setting["host"]:
            connection = http.client.HTTPSConnection(
                **proxy_setting, context=ssl._create_unverified_context()
            )
            connection.set_tunnel(url)
        else:
            connection = http.client.HTTPSConnection(url, context=ssl._create_unverified_context())
    else:
        if proxy_setting["host"]:
            connection = http.client.HTTPConnection(**proxy_setting)
            connection.set_tunnel(url)
        else:
            connection = http.client.HTTPConnection(url)

    return stream_response(connection, data, headers)
