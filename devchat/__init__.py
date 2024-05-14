import os

script_dir = os.path.dirname(os.path.realpath(__file__))
os.environ["TIKTOKEN_CACHE_DIR"] = os.path.join(script_dir, "tiktoken_cache")
