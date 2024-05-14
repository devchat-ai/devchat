import os
import re

from .namespace import Namespace


class RecursivePrompter:
    def __init__(self, namespace: Namespace):
        self.namespace = namespace

    def run(self, name: str) -> str:
        ancestors = name.split(".")
        merged_content = ""
        for index in range(len(ancestors)):
            ancestor_name = ".".join(ancestors[: index + 1])
            file_path = self.namespace.get_file(ancestor_name, "prompt.txt")
            if file_path:
                with open(file_path, "r", encoding="utf-8") as file:
                    prompt_content = file.read()
                    # replace @file@ with the content of the file
                    prompt_content = self._replace_file_references(file_path, prompt_content)
                    merged_content += prompt_content
                    merged_content += "\n"

        return merged_content

    def _replace_file_references(self, prompt_file_path: str, content: str) -> str:
        # prompt_file_path is the path to the file that contains the content
        # @relative file path@: file is relative to the prompt_file_path
        pattern = re.compile(r"@(.+?)@")
        matches = pattern.findall(content)
        for match in matches:
            file_path = os.path.join(os.path.dirname(prompt_file_path), match)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    file_content = file.read()
                    content = content.replace(f"@{match}@", file_content)
        return content
