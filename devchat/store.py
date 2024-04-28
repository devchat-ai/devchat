from dataclasses import asdict
import json
import os
from typing import List, Dict, Any, Optional
from tinydb import TinyDB, where, Query
from tinydb.table import Table
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
        self._chat_list_path = os.path.join(store_dir, 'prompts_list.json')
        self._db_path = os.path.join(store_dir, 'prompts.json')
        self._chat = chat

        if os.path.isfile(self._chat_list_path):
            with open(self._chat_list_path, 'r', encoding="utf-8") as fp:
                self._chat_lists = json.loads(fp.read())
        elif os.path.isfile(self._graph_path):
            # convert old graphml to new json
            from xml.etree.ElementTree import ParseError
            import networkx as nx
            try:
                graph = nx.read_graphml(self._graph_path)

                roots = [node for node in graph.nodes() if graph.out_degree(node) == 0]
                
                self._chat_lists = []
                for root in roots:
                    chat_list = [(root, graph.nodes[root]['timestamp'])]

                    ancestors = nx.ancestors(graph, root)
                    for ancestor in ancestors:
                        chat_list.append((ancestor, graph.nodes[ancestor]['timestamp']))
                
                    self._chat_lists.append(chat_list)

                with open(self._chat_list_path, 'w', encoding="utf-8") as fp:
                    fp.write(json.dumps(self._chat_lists))

                # rename graphml to json
                os.rename(self._graph_path, self._graph_path + '.bak')
                
            except ParseError as error:
                raise ValueError(f"Invalid file format for graph: {self._graph_path}") from error
        else:
            self._chat_lists = []

        self._db = TinyDB(self._db_path)
        self._db_meta = self._migrate_db()
        self._topics_table = self._db.table('topics')

        if not self._topics_table or not self._topics_table.all():
            self._initialize_topics_table()

    def _migrate_db(self) -> Table:
        """
        Migrate the database to the latest version.
        """
        metadata = self._db.table('metadata')

        result = metadata.get(where('version').exists())
        if not result or result['version'].startswith('0.1.'):
            def replace_response():
                def transform(doc):
                    if '_new_messages' not in doc or 'response' not in doc['_new_messages']:
                        logger.error("Prompt %s does not match '_new_messages.response'",
                                     doc['_hash'])
                    doc['_new_messages']['responses'] = doc['_new_messages'].pop('response')
                return transform

            logger.info("Migrating database from %s to 0.2.0", result)
            self._db.update(replace_response(),
                            Query()._new_messages.response.exists())  # pylint: disable=W0212
            metadata.insert({'version': '0.2.0'})
        return metadata

    def _initialize_topics_table(self):
        for chat_list in self._chat_lists:
            if not chat_list:
                continue

            first = chat_list[0]
            last  = chat_list[-1]

            self._topics_table.insert({
                'root': first[0],
                'latest_time': last[1],
                'title': None,
                'hidden': False
            })

    def _update_topics_table(self, prompt: Prompt):
        if prompt.parent:
            for chat_list in self._chat_lists:
                if not chat_list:
                    continue

                if chat_list[-1][0] == prompt.hash:
                    topic_hash = chat_list[0][0]
                    topic = next((t for t in self._topics_table if t['root'] == topic_hash), None)
                    if topic:
                        topic['latest_time'] = max(topic.get('latest_time', 0), prompt.timestamp)
                        self._topics_table.update(topic, doc_ids=[topic.doc_id])
                    break
        else:
            self._topics_table.insert({
                'root': prompt.hash,
                'latest_time': prompt.timestamp,
                'title': None,
                'hidden': False
            })

    def store_prompt(self, prompt: Prompt) -> str:
        """
        Store a prompt in the store.

        Args:
            prompt (Prompt): The prompt to store.
        """
        prompt.finalize_hash()

        # Store the prompt object in TinyDB
        self._db.insert(asdict(prompt))

        # Add the prompt to the graph
        topic_hash = None
        for chat_list in self._chat_lists:
            if not chat_list:
                continue
            if chat_list[-1][0] == prompt.parent:
                chat_list.append((prompt.hash, prompt.timestamp))
                topic_hash = chat_list[0][0]
                break
        
        if not topic_hash:
            topic_hash = prompt.hash
            self._chat_lists.append([(prompt.hash, prompt.timestamp)])
        self._update_topics_table(prompt)

        with open(self._chat_list_path, 'w', encoding="utf-8") as fp:
            fp.write(json.dumps(self._chat_lists))

        return topic_hash


    def get_prompt(self, prompt_hash: str) -> Prompt:
        """
        Retrieve a prompt from the store.

        Args:
            prompt_hash (str): The hash of the prompt to retrieve.
        Returns:
            Prompt: The retrieved prompt. None if the prompt is not found.
        """
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

        if not topic:
            return []

        sorted_nodes = []
        for chat_list in self._chat_lists:
            if not chat_list:
                continue

            if chat_list[0][0] != topic:
                continue

            sorted_nodes = chat_list.copy()
            sorted_nodes.reverse()

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

    def delete_prompt(self, prompt_hash: str) -> bool:
        """
        Delete a prompt from the store if it is a leaf.

        Args:
            prompt_hash (str): The hash of the prompt to delete.

        Returns:
            bool: True if the prompt is successfully deleted, False otherwise.
        """
        # Check if the prompt is a leaf
        for chat_list in self._chat_lists:
            if not chat_list:
                continue

            if chat_list[-1][0] != prompt_hash:
                continue

            chat_list.pop()

            # If the chat list is empty, remove it from the list of chat lists
            if not chat_list:
                self._chat_lists.remove(chat_list)

        # Update the topics table
        self._topics_table.remove(where('root') == prompt_hash)

        # Remove the prompt from the database
        self._db.remove(where('_hash') == prompt_hash)

        # Save the graph
        with open(self._chat_list_path, 'w', encoding="utf-8") as fp:
            fp.write(json.dumps(self._chat_lists))

        return True

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
