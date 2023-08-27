from .namespace import Namespace


class RecursivePrompter:
    def __init__(self, namespace: Namespace):
        self.namespace = namespace

    def run(self, name: str) -> str:
        ancestors = name.split('.')
        merged_content = ''
        for index in range(len(ancestors)):
            ancestor_name = '.'.join(ancestors[:index + 1])
            file_path = self.namespace.get_file(ancestor_name, 'prompt.txt')
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as file:
                    merged_content += file.read()
                    merged_content += '\n'
        return merged_content
