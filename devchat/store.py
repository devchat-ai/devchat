from dataclasses import asdict
import os
from typing import List, Dict, Any, Optional
from xml.etree.ElementTree import ParseError
import networkx as nx
from tinydb import TinyDB, where
from devchat.chat import Chat
from devchat.prompt import Prompt
from devchat.utils import get_logger

logger = get_logger(__name__)


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

    def _initialize_topics_table(self):
        roots = [node for node in self._graph.nodes() if self._graph.out_degree(node) == 0]
        for root in roots:
            ancestors = nx.ancestors(self._graph, root)
            if not ancestors:
                latest_time = self._graph.nodes[root]['timestamp']
            else:
                latest_time = max(self._graph.nodes[node]['timestamp'] for node in ancestors)
            self._topics_table.insert({
                'root': root,
                'latest_time': latest_time,
                'title': None,
                'hidden': False
            })

    def _update_topics_table(self, prompt: Prompt):
        if self._graph.in_degree(prompt.hash):
            logger.error("Prompt %s not a leaf to update topics table", prompt.hash)

        if prompt.parent:
            for topic in self._topics_table.all():
                if topic['root'] not in self._graph:
                    self._graph.add_node(topic['root'], timestamp=topic['latest_time'])
                    logger.warning("Topic %s not found in graph but added", topic['root'])
                if prompt.parent == topic['root'] or \
                        prompt.parent in nx.ancestors(self._graph, topic['root']):
                    topic['latest_time'] = max(topic['latest_time'], prompt.timestamp)
                    self._topics_table.update(topic, doc_ids=[topic.doc_id])
                    break
        else:
            self._topics_table.insert({
                'root': prompt.hash,
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

        for reference_hash in prompt.references:
            if reference_hash not in self._graph:
                logger.error("Reference %s not found while Prompt %s is stored to graph store.",
                             reference_hash, prompt.hash)

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

    def select_prompts(self, start: int, end: int, topic: Optional[str] = None) -> List[Prompt]:
        """
        Select recent prompts in reverse chronological order.

        Args:
            start (int): The start index.
            end (int): The end index (excluded).
            topic (Optional[str]): The hash of the root prompt of the topic.
                If set, select among the prompts of the topic.
        Returns:
            List[Prompt]: The list of prompts selected.
                If end is greater than the number of all prompts,
                the list will contain prompts from start to the end of the list.
        """
        if topic:
            ancestors = nx.ancestors(self._graph, topic)
            nodes_with_data = [(node, self._graph.nodes[node]) for node in ancestors] + \
                [(topic, self._graph.nodes[topic])]
            sorted_nodes = sorted(nodes_with_data, key=lambda x: x[1]['timestamp'], reverse=True)
        else:
            sorted_nodes = sorted(self._graph.nodes(data=True),
                                  key=lambda x: x[1]['timestamp'],
                                  reverse=True)

        prompts = []
        for node in sorted_nodes[start:end]:
            prompt = self.get_prompt(node[0])
            if not prompt:
                logger.error("Prompt %s not found while selecting from the store", node[0])
                continue
            prompts.append(prompt)
        return prompts

    def select_topics(self, start: int, end: int) -> List[Dict[str, Any]]:
        """
        Select recent topics in reverse chronological order.

        Args:
            start (int): The start index.
            end (int): The end index (excluded).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing root prompts
                with latest_time, and title fields.
        """
        visible_topics = self._topics_table.search(
            where('hidden') == False)  # pylint: disable=C0121
        sorted_topics = sorted(visible_topics, key=lambda x: x['latest_time'], reverse=True)

        topics = []
        for topic in sorted_topics[start:end]:
            prompt = self.get_prompt(topic['root'])
            if not prompt:
                logger.error("Topic %s not found while selecting from the store", topic['root'])
                continue
            topics.append({
                'root_prompt': prompt,
                'latest_time': topic['latest_time'],
                'title': topic['title'],
                'hidden': topic['hidden'],
            })
        return topics

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
