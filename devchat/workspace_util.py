import os
from typing import Optional

from .path import USER_CHAT_DIR


def _ensure_workspace_chat_dir(workspace_path: str) -> str:
    """
    Ensure the workspace chat directory exists and is ignored by git

    return the chat directory path
    """
    assert workspace_path, "workspace path is required to create .chat directory"
    chat_dir = os.path.join(workspace_path, ".chat")

    if not os.path.exists(chat_dir):
        try:
            os.makedirs(chat_dir, exist_ok=True)
        except FileExistsError:
            pass

    # ignore .chat dir in user's workspace
    ignore_file = os.path.join(chat_dir, ".gitignore")
    ignore_content = "*\n"
    if not os.path.exists(ignore_file):
        with open(ignore_file, "w") as f:
            f.write(ignore_content)

    return chat_dir


def get_workspace_chat_dir(workspace_path: Optional[str]) -> str:
    """
    Get the chat directory for a workspace
    Return user chat directory if workspace is None
    """
    workspace_chat_dir = USER_CHAT_DIR
    if workspace_path:
        workspace_chat_dir = _ensure_workspace_chat_dir(workspace_path)

    return workspace_chat_dir
