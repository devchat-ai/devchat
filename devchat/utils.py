import json
import logging
import os
import re
import getpass
import socket
import subprocess
from typing import List, Tuple, Optional
import datetime
import hashlib
import tiktoken

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def setup_logger(file_path: Optional[str] = None):
    """Utility function to set up a global file log handler."""
    if file_path is None:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(file_path)
    handler.setFormatter(log_formatter)
    logging.root.handlers = [handler]


def get_logger(name: str = None, handler: logging.Handler = None) -> logging.Logger:
    local_logger = logging.getLogger(name)

    # Default to 'INFO' if 'LOG_LEVEL' env is not set
    log_level_str = os.getenv('LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    local_logger.setLevel(log_level)

    # If a handler is provided, configure and add it to the logger
    if handler is not None:
        handler.setLevel(log_level)
        handler.setFormatter(log_formatter)
        local_logger.addHandler(handler)

    local_logger.info("Get %s", str(local_logger))
    return local_logger


def find_root_dir() -> Optional[str]:
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout.strip()
    except Exception:
        try:
            result = subprocess.run(["svn", "info"],
                                    capture_output=True, text=True, check=True, encoding='utf-8')
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Working Copy Root Path: "):
                        return line.split("Working Copy Root Path: ", 1)[1].strip()
        except Exception:
            return os.path.expanduser("~")
    return None


def git_ignore(target_dir: str, *ignore_entries: str) -> None:
    gitignore_path = os.path.join(target_dir, '.gitignore')

    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as gitignore_file:
            gitignore_content = gitignore_file.read()

        new_entries = []
        for entry in ignore_entries:
            if entry not in gitignore_content:
                new_entries.append(entry)

        if new_entries:
            with open(gitignore_path, 'a', encoding='utf-8') as gitignore_file:
                gitignore_file.write('\n# devchat\n')
                for entry in new_entries:
                    gitignore_file.write(f'{entry}\n')
    else:
        with open(gitignore_path, 'w', encoding='utf-8') as gitignore_file:
            gitignore_file.write('# devchat\n')
            for entry in ignore_entries:
                gitignore_file.write(f'{entry}\n')


def unix_to_local_datetime(unix_time) -> datetime.datetime:
    # Convert the Unix time to a naive datetime object in UTC
    naive_dt = datetime.datetime.utcfromtimestamp(unix_time).replace(tzinfo=datetime.timezone.utc)

    # Convert the UTC datetime object to the local timezone
    local_dt = naive_dt.astimezone()

    return local_dt


def get_user_info() -> Tuple[str, str]:
    try:
        cmd = ['git', 'config', 'user.name']
        user_name = subprocess.check_output(cmd, encoding='utf-8').strip()
    except Exception:
        user_name = getpass.getuser()

    try:
        cmd = ['git', 'config', 'user.email']
        user_email = subprocess.check_output(cmd, encoding='utf-8').strip()
    except Exception:
        user_email = user_name + '@' + socket.gethostname()

    return user_name, user_email


def user_id(user_name, user_email) -> Tuple[str, str]:
    user_str = f"{user_name} <{user_email}>"
    user_hash = hashlib.sha1(user_str.encode('utf-8')).hexdigest()
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
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            if not content:
                raise ValueError(f"File {file_path} is empty.")
            contents.append(content)
    return contents


def valid_hash(hash_str):
    """Check if a string is a valid hash value."""
    pattern = re.compile(r'^[a-f0-9]{64}$')  # for SHA-256 hash
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


def openai_message_tokens(message: dict, model: str) -> int:
    """Returns the number of tokens used by a message."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError as err:
        raise ValueError(f"Invalid model {model} for tiktoken.") from err

    num_tokens = 0
    if model == "gpt-3.5-turbo-0301":
        num_tokens += 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    else:
        num_tokens += 3
        tokens_per_name = 1

    for key, value in message.items():
        if key == 'function_call':
            value = json.dumps(value)
        if value:
            num_tokens += len(encoding.encode(value))
        if key == "name":
            num_tokens += tokens_per_name
    return num_tokens


def openai_response_tokens(message: dict, model: str) -> int:
    """Returns the number of tokens used by a response."""
    return openai_message_tokens(message, model)
