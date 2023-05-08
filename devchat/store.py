import os
import shelve
from typing import List
from xml.etree.ElementTree import ParseError
import networkx as nx
from devchat.prompt import Prompt


class Store:
    def __init__(self, store_dir: str):
        """
        Initializes a Store instance.

        Args:
            path (str): The folder to store the files containing the store.
        """
        store_dir = os.path.expanduser(store_dir)
        if not os.path.isdir(store_dir):
            os.makedirs(store_dir)
        self._graph_path = os.path.join(store_dir, 'prompts.graphml')
        self._db_path = os.path.join(store_dir, 'prompts.db')

        if os.path.isfile(self._graph_path):
            try:
                self._graph = nx.read_graphml(self._graph_path)
            except ParseError as error:
                raise ValueError(f"Invalid file format for graph: {self._graph_path}") from error
        else:
            self._graph = nx.DiGraph()

        self._db = shelve.open(self._db_path)

    @property
    def graph_path(self) -> str:
        """
        The path to the graph store file.
        """
        return self._graph_path

    @property
    def db_path(self) -> str:
        """
        The path to the object store file.
        """
        return self._db_path

    def store_prompt(self, prompt: Prompt):
        """
        Store a prompt in the store.

        Args:
            prompt (Prompt): The prompt to store.
        """
        if not prompt.hash:
            prompt.set_hash()

        # Add the prompt to the graph
        self._graph.add_node(prompt.hash, timestamp=prompt.timestamp)

        # Add edges for parents and references
        if prompt.parent:
            if prompt.parent not in self._graph:
                raise ValueError(f'Parent {prompt.parent} not found in the store.')
            self._graph.add_edge(prompt.hash, prompt.parent)
        for reference_hash in prompt.references:
            if reference_hash not in self._graph:
                raise ValueError(f'Reference {reference_hash} not found in the store.')
            self._graph.add_edge(prompt.hash, reference_hash)
        nx.write_graphml(self._graph, self._graph_path)

        # Store the prompt object in the shelve database
        self._db[prompt.hash] = prompt
        self._db.sync()

    def get_prompt(self, prompt_hash: str) -> Prompt:
        """
        Retrieve a prompt from the store.

        Args:
            prompt_hash (str): The hash of the prompt to retrieve.
        Returns:
            Prompt: The retrieved prompt.
        """
        if prompt_hash not in self._graph:
            raise ValueError(f'Prompt {prompt_hash} not found in the store.')

        # Retrieve the prompt object from the shelve database
        return self._db[prompt_hash]

    def select_recent(self, start: int, end: int) -> List[Prompt]:
        """
        Select recent prompts.

        Args:
            start (int): The start index.
            end (int): The end index (excluded).
        Returns:
            List[Prompt]: The list of prompts selected.
                          If end is greater than the number of all prompts,
                          the list will contain prompts from start to the end of the list.
        """
        sorted_nodes = sorted(self._graph.nodes(data=True),
                              key=lambda x: x[1]['timestamp'],
                              reverse=True)
        if end > len(sorted_nodes):
            end = len(sorted_nodes)
        return [self.get_prompt(note[0]) for note in sorted_nodes[start:end]]
