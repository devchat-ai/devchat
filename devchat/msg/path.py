import os

# -------------------------------
# devchat basic paths
# -------------------------------
USE_DIR = os.path.expanduser("~")
CHAT_DIR = os.path.join(USE_DIR, ".chat")

# -------------------------------
# workspace path (repo path)
# -------------------------------
# TODO: tmp hard code, will be passed from client or setup when starting the server
WORKSPACE_DIR = "/Users/kagami/Projects/merico/chat/"
WORKSPACE_CHAT_DIR = os.path.join(WORKSPACE_DIR, ".chat") 