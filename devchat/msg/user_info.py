import getpass
import os
import socket
import subprocess
from typing import Optional, Tuple


class UserInfo:
    def __init__(self):
        self._name = None
        self._email = None

        self._load_user_info()

    @property
    def name(self) -> str:
        if not self._name:
            self._load_user_info()

        return self._name

    @property
    def email(self) -> str:
        if not self._email:
            self._load_user_info()

        return self._email

    def _load_user_info(self):
        """
        Load user info
        """
        git_name, git_email = self.__get_git_user_info()

        if git_name and git_email:
            self._name = git_name
            self._email = git_email
            return

        sys_name = self.__get_sys_user_name()
        name = git_name or sys_name

        mock_email = name + "@" + socket.gethostname()
        email = git_email or mock_email

        self._name = name
        self._email = email
        return

    def __get_git_user_info(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Load user info from git
        """
        name, email = None, None
        try:
            cmd = ["git", "config", "user.name"]
            name = subprocess.check_output(cmd, encoding="utf-8").strip()
        except Exception:
            pass

        try:
            cmd = ["git", "config", "user.email"]
            email = subprocess.check_output(cmd, encoding="utf-8").strip()
        except Exception:
            pass

        return name, email

    def __get_sys_user_name(self) -> str:
        """
        Get user name from system
        """
        name = "devchat_anonymous"
        try:
            name = getpass.getuser()
        except Exception:
            user_dir = os.path.expanduser("~")
            name = user_dir.split(os.sep)[-1]

        return name


user_info = UserInfo()
