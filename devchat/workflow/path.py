import os

# -------------------------------
# devchat basic paths
# -------------------------------
USE_DIR = os.path.expanduser("~")
CHAT_DIR = os.path.join(USE_DIR, ".chat")


# -------------------------------
# workflow scripts paths
# -------------------------------
WORKFLOWS_BASE_NAME = "new_wf"
WORKFLOWS_BASE = os.path.join(CHAT_DIR, WORKFLOWS_BASE_NAME)  # TODO: a temporary name

MERICO_WORKFLOWS = os.path.join(WORKFLOWS_BASE, "merico", "workflows")
CUSTOM_WORKFLOWS = os.path.join(WORKFLOWS_BASE, "custom", "workflows")
COMMUNITY_WORKFLOWS = os.path.join(WORKFLOWS_BASE, "community", "workflows")

COMMAND_FILENAMES = ["command.yml", "command.yaml"]

# the priority order of the workflows when naming conflicts
PrioritizedWorkflows = [
    CUSTOM_WORKFLOWS,
    MERICO_WORKFLOWS,
    COMMUNITY_WORKFLOWS,
]


# -------------------------------
#  Python environments paths
# -------------------------------
MAMBA_ROOT = os.path.join(CHAT_DIR, "mamba")
MAMBA_PY_ENVS = os.path.join(MAMBA_ROOT, "envs")
