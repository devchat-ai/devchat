import os
import sys
import subprocess
from typing import Optional, Dict

from .envs import MAMBA_BIN_PATH
from .path import MAMBA_PY_ENVS, MAMBA_ROOT
from .user_setting import USER_SETTINGS
from .schema import ExternalPyConf


# CONDA_FORGE = [
#     "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/",
#     "conda-forge",
# ]
CONDA_FORGE_TUNA = "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/"
PYPI_TUNA = "https://pypi.tuna.tsinghua.edu.cn/simple"


def _get_external_envs() -> Dict[str, ExternalPyConf]:
    """
    Get the external python environments info from the user settings.
    """
    external_pythons: Dict[str, ExternalPyConf] = {}
    for conf in USER_SETTINGS.external_workflow_python:
        external_pythons[conf.env_name] = conf

    return external_pythons

EXTERNAL_ENVS = _get_external_envs()

class PyEnvManager:
    mamba_bin = MAMBA_BIN_PATH
    mamba_root = MAMBA_ROOT

    def __init__(self):
        pass

    @staticmethod
    def get_py_version(py: str) -> Optional[str]:
        """
        Get the version of the python executable.
        """
        py_version_cmd = [py, "--version"]
        with subprocess.Popen(
            py_version_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            proc.wait()

            if proc.returncode != 0:
                return None

            out = proc.stdout.read().decode("utf-8")
            return out.split()[1]

    def install(self, env_name: str, requirements_file: str) -> bool:
        """
        Install requirements into the python environment.

        Args:
            requirements: the absolute path to the requirements file.
        """
        py = self.get_py(env_name)
        if not py:
            # TODO: raise error?
            return False

        if not os.path.exists(requirements_file):
            # TODO: raise error?
            return False

        cmd = [
            py,
            "-m",
            "pip",
            "install",
            "-r",
            requirements_file,
            "-i",
            PYPI_TUNA,
        ]
        env = os.environ.copy()
        env.pop("PYTHONPATH")
        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        ) as proc:
            proc.wait()

            if proc.returncode != 0:
                print(
                    f"Failed to install requirements: {requirements_file}", flush=True
                )
                return False

            return True

    def ensure(self, env_name: str, py_version: str) -> Optional[str]:
        """
        Ensure the python environment exists with the given name and version.

        return the python executable path.
        """
        py = self.get_py(env_name)
        should_remove = False

        if py:
            # check the version of the python executable
            current_version = self.get_py_version(py)

            if current_version == py_version:
                return py

            should_remove = True

        print("\n```Step\n# Setting up workflow environment", flush=True)
        print(f"\nenv_name: {env_name}")
        print(f"python: {py_version}", flush=True)

        if should_remove:
            self.remove(env_name)

        # create the environment
        create_ok = self.create(env_name, py_version)
        print("\n```", flush=True)

        if not create_ok:
            return None
        return self.get_py(env_name)

    def create(self, env_name: str, py_version: str) -> bool:
        """
        Create a new python environment using mamba.
        """
        is_exist = os.path.exists(os.path.join(MAMBA_PY_ENVS, env_name))
        if is_exist:
            return True

        # create the environment
        cmd = [
            self.mamba_bin,
            "create",
            "-n",
            env_name,
            "-c",
            CONDA_FORGE_TUNA,
            "-r",
            self.mamba_root,
            f"python={py_version}",
            "-y",
        ]
        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            proc.wait()

            if proc.returncode != 0:
                return False

            return True

    def remove(self, env_name: str) -> bool:
        """
        Remove the python environment.
        """
        is_exist = os.path.exists(os.path.join(MAMBA_PY_ENVS, env_name))
        if not is_exist:
            return True

        # remove the environment
        cmd = [
            self.mamba_bin,
            "env",
            "remove",
            "-n",
            env_name,
            "-r",
            self.mamba_root,
            "-y",
        ]
        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            proc.wait()

            if proc.returncode != 0:
                return False

            return True

    def get_py(self, env_name: str) -> Optional[str]:
        """
        Get the python executable path of the given environment.
        """
        env_path = None
        if sys.platform == "win32":
            env_path = os.path.join(MAMBA_PY_ENVS, env_name, "python.exe")
            # env_path = os.path.join(MAMBA_PY_ENVS, env_name, "Scripts", "python.exe")
        else:
            env_path = os.path.join(MAMBA_PY_ENVS, env_name, "bin", "python")

        if env_path and os.path.exists(env_path):
            return env_path

        return None
