import datetime
import getpass
import hashlib
import logging
import os
import re
import socket
import subprocess
from typing import List, Optional, Tuple

log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
encoding = None


def setup_logger(file_path: Optional[str] = None):
    """Utility function to set up a global file log handler."""
    if file_path is None:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(file_path)
    handler.setFormatter(log_formatter)
    logging.root.handlers = [handler]


def get_logging_file() -> Optional[str]:
    """
    Get the file path of the global file log handler.
    """
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            return handler.baseFilename
    return None


def get_logger(name: str = None, handler: logging.Handler = None) -> logging.Logger:
    local_logger = logging.getLogger(name)

    # Default to 'INFO' if 'LOG_LEVEL' env is not set
    log_level_str = os.getenv("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    local_logger.setLevel(log_level)

    # If a handler is provided, configure and add it to the logger
    if handler is not None:
        handler.setLevel(log_level)
        handler.setFormatter(log_formatter)
        local_logger.addHandler(handler)

    local_logger.info("Get %s", str(local_logger))
    return local_logger


def find_root_dir() -> Tuple[Optional[str], Optional[str]]:
    """
    Find the root directory of the repository and the user's home directory
    """
    try:
        user_dir = os.path.expanduser("~")
        if not os.path.isdir(user_dir):
            user_dir = None
    except Exception:
        user_dir = None

    repo_dir = None
    try:
        repo_dir = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        ).stdout.strip()
        if not os.path.isdir(repo_dir):
            repo_dir = None
        else:
            return repo_dir, user_dir
    except Exception:
        repo_dir = None

    try:
        result = subprocess.run(
            ["svn", "info"], capture_output=True, text=True, check=True, encoding="utf-8"
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Working Copy Root Path: "):
                    repo_dir = line.split("Working Copy Root Path: ", 1)[1].strip()
                    if os.path.isdir(repo_dir):
                        return repo_dir, user_dir
    except Exception:
        repo_dir = None

    return repo_dir, user_dir


def add_gitignore(target_dir: str, *ignore_entries: str) -> None:
    gitignore_path = os.path.join(target_dir, ".gitignore")

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as gitignore_file:
            gitignore_content = gitignore_file.read()

        new_entries = []
        for entry in ignore_entries:
            if entry not in gitignore_content:
                new_entries.append(entry)

        if new_entries:
            with open(gitignore_path, "a", encoding="utf-8") as gitignore_file:
                gitignore_file.write("\n# devchat\n")
                for entry in new_entries:
                    gitignore_file.write(f"{entry}\n")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as gitignore_file:
            gitignore_file.write("# devchat\n")
            for entry in ignore_entries:
                gitignore_file.write(f"{entry}\n")


def unix_to_local_datetime(unix_time) -> datetime.datetime:
    # Convert the Unix time to a naive datetime object in UTC
    naive_dt = datetime.datetime.utcfromtimestamp(unix_time).replace(tzinfo=datetime.timezone.utc)

    # Convert the UTC datetime object to the local timezone
    local_dt = naive_dt.astimezone()

    return local_dt


def get_user_info() -> Tuple[str, str]:
    try:
        cmd = ["git", "config", "user.name"]
        user_name = subprocess.check_output(cmd, encoding="utf-8").strip()
    except Exception:
        try:
            user_name = getpass.getuser()
        except Exception:
            user_dir = os.path.expanduser("~")
            user_name = user_dir.split(os.sep)[-1]

    try:
        cmd = ["git", "config", "user.email"]
        user_email = subprocess.check_output(cmd, encoding="utf-8").strip()
    except Exception:
        user_email = user_name + "@" + socket.gethostname()

    return user_name, user_email


def user_id(user_name, user_email) -> Tuple[str, str]:
    user_str = f"{user_name} <{user_email}>"
    user_hash = hashlib.sha1(user_str.encode("utf-8")).hexdigest()
    return user_str, user_hash


def parse_files(file_paths: List[str]) -> List[str]:
    if not file_paths:
        return []

    for file_path in file_paths:
        file_path = os.path.expanduser(file_path.strip())
        if not os.path.isfile(file_path):
            raise ValueError(f"File {file_path} does not exist.")

    contents = []
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            if not content:
                raise ValueError(f"File {file_path} is empty.")
            contents.append(content)
    return contents


def valid_hash(hash_str):
    """Check if a string is a valid hash value."""
    pattern = re.compile(r"^[a-f0-9]{64}$")  # for SHA-256 hash
    return bool(pattern.match(hash_str))


def check_format(formatted_response) -> bool:
    pattern = r"(User: .+ <.+@.+>\nDate: .+\n\n(?:.*\n)*\n(?:prompt [a-f0-9]{64}\n\n?)+)"
    return bool(re.fullmatch(pattern, formatted_response))


def get_content(formatted_response) -> str:
    header_pattern = r"User: .+ <.+@.+>\nDate: .+\n\n"
    footer_pattern = r"\n(?:prompt [a-f0-9]{64}\n\n?)+"

    content = re.sub(header_pattern, "", formatted_response)
    content = re.sub(footer_pattern, "", content)

    return content


def get_prompt_hash(formatted_response) -> str:
    if not check_format(formatted_response):
        raise ValueError("Invalid formatted response.")
    footer_pattern = r"\n(?:prompt [a-f0-9]{64}\n\n?)+"
    # get the last prompt hash
    prompt_hash = re.findall(footer_pattern, formatted_response)[-1].strip()
    prompt_hash = prompt_hash.replace("prompt ", "")
    return prompt_hash


def update_dict(dict_to_update, key, value) -> dict:
    """
    Update a dictionary with a key-value pair and return the dictionary.
    """
    dict_to_update[key] = value
    return dict_to_update


def openai_message_tokens(messages: dict, model: str) -> int:
    """Returns the number of tokens used by a message."""
    if not os.environ.get("USE_TIKTOKEN", False):
        return len(str(messages)) / 4

    global encoding
    if not encoding:
        import tiktoken

        script_dir = os.path.dirname(os.path.realpath(__file__))
        os.environ["TIKTOKEN_CACHE_DIR"] = os.path.join(script_dir, "tiktoken_cache")

        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            from tiktoken import registry
            from tiktoken.core import Encoding
            from tiktoken.registry import _find_constructors

            def get_encoding(name: str):
                _find_constructors()
                constructor = registry.ENCODING_CONSTRUCTORS[name]
                return Encoding(**constructor(), use_pure_python=True)

            encoding = get_encoding("cl100k_base")

    return len(encoding.encode(str(messages), disallowed_special=()))


def openai_response_tokens(message: dict, model: str) -> int:
    """Returns the number of tokens used by a response."""
    return openai_message_tokens(message, model)


def rmtree(path: str) -> None:
    import shutil

    def __onerror(func, path, _1):
        """
        Error handler for shutil.rmtree.

        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.

        If the error is for another reason it re-raises the error.

        Usage : shutil.rmtree(path, onerror=onerror)
        """
        import os
        import stat

        # Check if file access issue
        if not os.access(path, os.W_OK):
            # Try to change the file to be writable (remove read-only flag)
            os.chmod(path, stat.S_IWUSR)
            # Retry the function that failed
            func(path)

    shutil.rmtree(path, onerror=__onerror)
