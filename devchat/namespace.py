import os
from typing import List, Optional
import re


class Namespace:
    def __init__(self, root_path: str,
                 branches: List[str] = None):
        """
        :param root_path: The root path of the namespace.
        :param branches: The hidden branches with ascending order of priority.
        """
        self.root_path = root_path
        self.branches = branches if branches else ['sys', 'org', 'usr']

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """
        Check if a name is valid.

        A valid name is either an empty string or
        a sequence of one or more alphanumeric characters, hyphens, or underscores,
        separated by single dots. Each component cannot contain a dot.

        :param name: The name to check.
        :return: True if the name is valid, False otherwise.
        """
        # The regular expression pattern for a valid name
        if name is None:
            return False
        pattern = r'^$|^(?!.*\.\.)[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)*$'
        return bool(re.match(pattern, name))

    def get_files(self, name: str) -> Optional[List[str]]:
        """
        :param name: The command name in the namespace.
        :return: The full paths of the files in the command directory.
        """
        if not self.is_valid_name(name):
            return None
        # Convert the dot-separated name to a path
        path = os.path.join(*name.split('.'))
        files = {}
        path_found = False
        for branch in self.branches:
            full_path = os.path.join(self.root_path, branch, path)
            if os.path.isdir(full_path):
                # If it exists and is a directory, get the files
                path_found = True
                for file in os.listdir(full_path):
                    files[file] = os.path.join(full_path, file)
        # If no existing path is found, return None
        if not path_found:
            return None
        # If path is found but no files exist, return an empty list
        # Sort the files in alphabetical order before returning
        return sorted(files.values()) if files else []

    def list_names(self, name: str = '', recursive: bool = False) -> Optional[List[str]]:
        """
        :param name: The command name in the namespace. Defaults to the root.
        :param recursive: Whether to list all descendant names or only child names.
        :return: A list of all names under the given name, or None if the name is invalid.
        """
        if not self.is_valid_name(name):
            return None
        commands = set()
        path = os.path.join(*name.split('.'))
        found = False
        for branch in self.branches:
            full_path = os.path.join(self.root_path, branch, path)
            if os.path.isdir(full_path):
                found = True
                self._add_dirnames_to_commands(full_path, name, commands)
                if recursive:
                    self._add_recursive_dirnames_to_commands(full_path, name, commands)
        return sorted(commands) if found else None

    def _add_dirnames_to_commands(self, full_path: str, name: str, commands: set):
        for dirname in os.listdir(full_path):
            command_name = '.'.join([name, dirname]) if name else dirname
            commands.add(command_name)

    def _add_recursive_dirnames_to_commands(self, full_path: str, name: str, commands: set):
        for dirpath, dirnames, _ in os.walk(full_path):
            for dirname in dirnames:
                relative_path = os.path.relpath(dirpath, full_path).replace(os.sep, '.')
                if relative_path != '.':
                    command_name = ('.'.join([name, relative_path, dirname])
                                    if name else '.'.join([relative_path, dirname]))
                else:
                    command_name = '.'.join([name, dirname]) if name else dirname
                commands.add(command_name)
