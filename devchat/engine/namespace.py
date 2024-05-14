import os
import re
from typing import List, Optional


class Namespace:
    def __init__(self, root_path: str, branches: List[str] = None):
        """
        :param root_path: The root path of the namespace.
        :param branches: The hidden branches with ascending order of priority.
        """
        self.root_path = root_path
        self.branches = branches if branches else ["sys", "org", "usr"]

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
        pattern = r"^$|^(?!.*\.\.)[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)*$"
        return bool(re.match(pattern, name))

    def get_file(self, name: str, file: str) -> Optional[str]:
        """
        :param name: The command name in the namespace.
        :param file: The target file name.
        :return: The full path of the target file in the command directory.
        """
        if not self.is_valid_name(name):
            return None
        # Convert the dot-separated name to a path
        path = os.path.join(*name.split("."))
        for branch in reversed(self.branches):
            full_path = os.path.join(self.root_path, branch, path)
            if os.path.isdir(full_path):
                # If it exists and is a directory, check for the file
                file_path = os.path.join(full_path, file)
                if os.path.isfile(file_path):
                    # If the file exists, return its path
                    return file_path
        # If no file is found, return None
        return None

    def list_files(self, name: str) -> List[str]:
        """
        :param name: The command name in the namespace.
        :return: The full paths of the files in the command directory.
        """
        if not self.is_valid_name(name):
            raise ValueError(f"Invalid name to list files: {name}")
        # Convert the dot-separated name to a path
        path = os.path.join(*name.split("."))
        files = {}
        path_found = False
        for branch in self.branches:
            full_path = os.path.join(self.root_path, branch, path)
            if os.path.isdir(full_path):
                # If it exists and is a directory, get the files
                path_found = True
                for file in os.listdir(full_path):
                    files[file] = os.path.join(full_path, file)
        # If no existing path is found, raise an error
        if not path_found:
            raise ValueError(f"Path not found to list files: {name}")
        # If path is found but no files exist, return an empty list
        # Sort the files in alphabetical order before returning
        return sorted(files.values()) if files else []

    def list_names(self, name: str = "", recursive: bool = False) -> List[str]:
        """
        :param name: The command name in the namespace. Defaults to the root.
        :param recursive: Whether to list all descendant names or only child names.
        :return: A list of all names under the given name.
        """
        if not self.is_valid_name(name):
            raise ValueError(f"Invalid name to list names: {name}")
        commands = set()
        path = os.path.join(*name.split("."))
        found = False
        for branch in self.branches:
            full_path = os.path.join(self.root_path, branch, path)
            if os.path.isdir(full_path):
                found = True
                self._add_dirnames_to_commands(full_path, name, commands)
                if recursive:
                    self._add_recursive_dirnames_to_commands(full_path, name, commands)
        if not found:
            raise ValueError(f"Path not found to list names: '{name}'")
        return sorted(commands)

    def _add_dirnames_to_commands(self, full_path: str, name: str, commands: set):
        for dirname in os.listdir(full_path):
            if dirname.startswith("."):
                continue
            if os.path.isdir(os.path.join(full_path, dirname)):
                command_name = ".".join([name, dirname]) if name else dirname
                commands.add(command_name)

    def _add_recursive_dirnames_to_commands(self, full_path: str, name: str, commands: set):
        self._recursive_dir_walk(full_path, name, commands)

    def _recursive_dir_walk(self, full_path: str, name: str, commands: set):
        for dirname in os.listdir(full_path):
            if dirname.startswith("."):
                continue
            dir_path = os.path.join(full_path, dirname)
            if os.path.isdir(dir_path):
                command_name = ".".join([name, dirname]) if name else dirname
                commands.add(command_name)
                self._recursive_dir_walk(dir_path, command_name, commands)
