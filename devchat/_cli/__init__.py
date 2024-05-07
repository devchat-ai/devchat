import os
from .log import log
from .prompt import prompt
from .run import run
from .topic import topic
from .route import route
from .command import commands, command, Command

script_dir = os.path.dirname(os.path.realpath(__file__))
os.environ['TIKTOKEN_CACHE_DIR'] = os.path.join(script_dir, '..', 'tiktoken_cache')

__all__ = [
    'log',
    'prompt',
    'run',
    'topic',
	'route',
    'commands',
    'command',
    'Command'
]
