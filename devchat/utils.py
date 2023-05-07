import os
import re
import getpass
import socket
import subprocess
from typing import List, Tuple
import datetime
import pytz
from dateutil import tz


def find_git_root():
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
        return root.decode("utf-8").strip()
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Not inside a Git repository") from error


def git_ignore(git_root_dir, *ignore_entries):
    gitignore_path = os.path.join(git_root_dir, '.gitignore')

    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as gitignore_file:
            gitignore_content = gitignore_file.read()

        new_entries = []
        for entry in ignore_entries:
            relative_entry = os.path.relpath(entry, git_root_dir)
            if relative_entry not in gitignore_content:
                new_entries.append(relative_entry)

        if new_entries:
            with open(gitignore_path, 'a', encoding='utf-8') as gitignore_file:
                gitignore_file.write('\n# DevChat\n')
                for entry in new_entries:
                    gitignore_file.write(f'{entry}\n')
    else:
        with open(gitignore_path, 'w', encoding='utf-8') as gitignore_file:
            gitignore_file.write('# DevChat\n')
            for entry in ignore_entries:
                relative_entry = os.path.relpath(entry, git_root_dir)
                gitignore_file.write(f'{relative_entry}\n')


def unix_to_local_datetime(unix_time) -> datetime.datetime:
    # Get the local time zone
    local_tz = tz.tzlocal()

    # Convert the Unix time to a naive datetime object
    naive_dt = datetime.datetime.utcfromtimestamp(unix_time)

    # Localize the naive datetime object to the local time zone
    local_dt = naive_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)

    return local_dt


def get_git_user_info() -> Tuple[str, str]:
    try:
        cmd = ['git', 'config', 'user.name']
        git_user_name = subprocess.check_output(cmd).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        git_user_name = getpass.getuser()

    try:
        cmd = ['git', 'config', 'user.email']
        git_user_email = subprocess.check_output(cmd).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        git_user_email = git_user_name + '@' + socket.gethostname()

    return git_user_name, git_user_email


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


def is_valid_hash(hash_str):
    """Check if a string is a valid hash value."""
    # Hash values are usually alphanumeric with a fixed length
    # depending on the algorithm used to generate them
    pattern = re.compile(r'^[a-fA-F0-9]{40}$')  # Example pattern for SHA-1 hash
    return bool(pattern.match(hash_str))


def validate_hashes(hashes: List[str]) -> List[str]:
    if hashes:
        for value in hashes:
            if not is_valid_hash(value):
                raise ValueError(f"Invalid hash value {value}.")
    return hashes


def update_dict(dict_to_update, key, value) -> dict:
    """
    Update a dictionary with a key-value pair and return the dictionary.
    """
    dict_to_update[key] = value
    return dict_to_update
