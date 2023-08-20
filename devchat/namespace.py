import os
from typing import List, Optional


class Namespace:
    def __init__(self, root_path: str,
                 branches: List[str] = None):
        """
        :param root_path: The root path of the namespace.
        :param branches: The hidden branches with descending order of priority.
        """
        self.root_path = root_path
        self.branches = branches if branches else ['usr', 'org', 'sys']

    def get_path(self, name: str) -> Optional[str]:
        """
        :param name: The command name in the namespace.
        :return: The relative path of the command directory.
        """
        if not name:
            return None
        # Convert the dot-separated name to a path
        path = os.path.join(*name.split('.'))

        for branch in self.branches:
            full_path = os.path.join(self.root_path, branch, path)
            if os.path.exists(full_path):
                # If it exists, return the branch/path part
                return os.path.join(branch, path)
        # If no existing path is found, return None
        return None
