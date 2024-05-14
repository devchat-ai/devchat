import os

from .log import log
from .prompt import prompt
from .route import route
from .run import run
from .topic import topic

script_dir = os.path.dirname(os.path.realpath(__file__))
os.environ["TIKTOKEN_CACHE_DIR"] = os.path.join(script_dir, "..", "tiktoken_cache")

__all__ = [
    "log",
    "prompt",
    "run",
    "topic",
    "route",
]
