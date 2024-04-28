import os

# -------------------------------
# devchat basic paths
# -------------------------------
USE_DIR = os.path.expanduser("~")
CHAT_DIR = os.path.join(USE_DIR, ".chat")


# -------------------------------
# workflow scripts paths
# -------------------------------
WORKFLOWS_BASE_NAME = "scripts"
WORKFLOWS_BASE = os.path.join(CHAT_DIR, WORKFLOWS_BASE_NAME)  # TODO: a temporary name
WORKFLOWS_CONFIG_FILENAME = "config.yml"

MERICO_WORKFLOWS = os.path.join(WORKFLOWS_BASE, "merico")
COMMUNITY_WORKFLOWS = os.path.join(WORKFLOWS_BASE, "community")

COMMAND_FILENAMES = ["command.yml", "command.yaml"]

CUSTOM_BASE = os.path.join(WORKFLOWS_BASE, "custom")
CUSTOM_CONFIG_FILE = os.path.join(CUSTOM_BASE, "config.yml")


# -------------------------------
#  Python environments paths
# -------------------------------
MAMBA_ROOT = os.path.join(CHAT_DIR, "mamba")
MAMBA_PY_ENVS = os.path.join(MAMBA_ROOT, "envs")
