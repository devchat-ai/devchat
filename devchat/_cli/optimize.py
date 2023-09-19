import requests

requests_get = requests.get
def get(url, params=None, **kwargs):
    if url.startswith('https://raw.githubusercontent.com'):
        raise requests.ConnectionError
    return requests_get(url, params, **kwargs)
requests.get = get

import sys
sys_out = sys.stdout
sys.stdout = None
import litellm
sys.stdout = sys_out