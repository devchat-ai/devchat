import requests

requests_get = requests.get
def get(url, params=None, **kwargs):
    if url.startswith('https://raw.githubusercontent.com'):
        raise requests.ConnectionError
    return requests_get(url, params, **kwargs) # pylint: disable=W3101
requests.get = get

import sys # pylint: disable=C0413,C0411
sys_out = sys.stdout
sys.stdout = None
import litellm # pylint: disable=C0413,W0611
sys.stdout = sys_out
