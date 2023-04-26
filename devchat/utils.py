import re
import os
import socket
import subprocess
from typing import Tuple
import datetime
import pytz
from dateutil import tz


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
        git_user_name = os.getlogin()

    try:
        cmd = ['git', 'config', 'user.email']
        git_user_email = subprocess.check_output(cmd).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        git_user_email = git_user_name + '@' + socket.gethostname()

    return git_user_name, git_user_email


def is_valid_hash(hash_str):
    """Check if a string is a valid hash value."""
    # Hash values are usually alphanumeric with a fixed length
    # depending on the algorithm used to generate them
    pattern = re.compile(r'^[a-fA-F0-9]{40}$')  # Example pattern for SHA-1 hash
    return bool(pattern.match(hash_str))
