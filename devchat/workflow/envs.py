"""
Explicitly define the environment variables used in the workflow engine.
"""

import os

PYTHON_PATH = os.environ.get("PYTHONPATH", "")
DEVCHAT_PYTHON_PATH = os.environ.get("DEVCHAT_PYTHONPATH", PYTHON_PATH)

# the path to the mamba binary
MAMBA_BIN_PATH = os.environ.get("MAMBA_BIN_PATH", "")
