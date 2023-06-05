from dataclasses import asdict
import logging
import os
from typing import List
from xml.etree.ElementTree import ParseError
import networkx as nx
from tinydb import TinyDB, where
from devchat.chat import Chat
from devchat.prompt import Prompt

logger = logging.getLogger(__name__)


class Store:
    def __init__(self, store_dir: str, chat: Chat):
        """
        Initializes a Store instance.

        Args:
            store_dir (str): The folder to store the files containing the store.
            chat (Chat): The Chat instance.
        """
        store_dir = os.path.expanduser(store_dir)
        if not os.path.isdir(store_dir):
            os.makedirs(store_dir)

        self._graph_path = os.path.join(store_dir, 'prompts.graphml')
        self._db_path = os.path.join(store_dir, 'prompts.json')
        self._chat = chat

        if os.path.isfile(self._graph_path):
            try:
                self._graph = nx.read_graphml(self._graph_path)
            except ParseError as error:
                raise ValueError(f"Invalid file format for graph: {self._graph_path}") from error
        else:
            self._graph = nx.DiGraph()

        self._db = TinyDB(self._db_path)
        self._topics_table = self._db.table('topics')

        if not self._topics_table or self._topics_table.all() == []:
            self._initialize_topics_table()

    def _roots(self) -> List[object]:
        graph = self._graph
        return [node for node in graph.nodes() if graph.out_degree(node) == 0]

    def _leaves(self) -> List[object]:
        graph = self._graph
        return [node for node in graph.nodes() if graph.in_degree(node) == 0]

    def _initialize_topics_table(self):
        roots = self._roots()
        all_leaves = self._leaves()
        root_to_leaves = {root: [] for root in roots}

        for leaf in all_leaves:
            root = next(nx.descendants(self._graph, leaf).intersection(roots))
            root_to_leaves[root].append(leaf)

        for root, leaves in root_to_leaves.items():
            latest_time = max(self._graph.nodes[leaf]['timestamp'] for leaf in leaves)
            self._topics_table.insert({
                'root': root,
                'leaves': leaves,
                'latest_time': latest_time,
                'title': None,
                'hidden': False
            })

    def _update_topics_table(self, prompt: Prompt):
        if self._graph.in_degree(prompt):
            logger.error("Prompt %s not a leaf to update topics table", prompt.hash)

        if prompt.parent:
            topic = next((topic for topic in self._topics_table.all()
                          if prompt.parent in topic['leaves']), None)
            if topic:
                topic['leaves'].remove(prompt.parent)
                topic['leaves'].append(prompt.hash)
                topic['latest_time'] = max(topic['latest_time'], prompt.timestamp)
                self._topics_table.update(topic, doc_ids=[topic.doc_id])
            else:
                logger.error("Parent %s of prompt %s not found in topic leaves",
                             prompt.parent, prompt.hash)
        else:
            self._topics_table.insert({
                'root': prompt.hash,
                'leaves': [prompt.hash],
                'latest_time': prompt.timestamp,
                'title': None,
                'hidden': False
            })

    def store_prompt(self, prompt: Prompt):
        """
        Store a prompt in the store.

        Args:
            prompt (Prompt): The prompt to store.
        """
        if not prompt.hash:
            prompt.set_hash()

        # Store the prompt object in TinyDB
        self._db.insert(asdict(prompt))

        # Add the prompt to the graph
        self._graph.add_node(prompt.hash, timestamp=prompt.timestamp)

        # Add edges for parents and references
        if prompt.parent:
            if prompt.parent not in self._graph:
                logger.error("Parent %s not found while Prompt %s is stored to graph store.",
                             prompt.parent, prompt.hash)
            else:
                self._graph.add_edge(prompt.hash, prompt.parent)
                self._update_topics_table(prompt)
        else:
            self._topics_table.insert({
                'ancestor_hash': prompt.hash,
                'descendant_hash': prompt.hash,
                'latest_time': prompt.timestamp,
                'title': None,
                'hidden': False
            })

        for reference_hash in prompt.references:
            if reference_hash not in self._graph:
                logger.warning("Reference %s not found while Prompt %s is stored to graph store.",
                               reference_hash, prompt.hash)
            else:
                self._graph.add_edge(prompt.hash, reference_hash)
        nx.write_graphml(self._graph, self._graph_path)

    def get_prompt(self, prompt_hash: str) -> Prompt:
        """
        Retrieve a prompt from the store.

        Args:
            prompt_hash (str): The hash of the prompt to retrieve.
        Returns:
            Prompt: The retrieved prompt. None if the prompt is not found.
        """
        if prompt_hash not in self._graph:
            logger.warning("Prompt %s not found while retrieving from graph store.", prompt_hash)
            return None

        # Retrieve the prompt object from TinyDB
        prompt_data = self._db.search(where('_hash') == prompt_hash)
        if not prompt_data:
            logger.warning("Prompt %s not found while retrieving from object store.", prompt_hash)
            return None
        assert len(prompt_data) == 1
        return self._chat.load_prompt(prompt_data[0])

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
        prompts = []
        for node in sorted_nodes[start:end]:
            prompt = self.get_prompt(node[0])
            if not prompt:
                logger.error("Prompt %s not found while selecting from the store.", node[0])
                continue
            prompts.append(prompt)
        return prompts

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
