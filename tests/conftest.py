import os
import shutil
import tempfile
import pytest
from git import Repo


@pytest.fixture(name='git_repo', scope='module')
def fixture_git_repo(request):
    # Create a temporary directory
    repo_dir = tempfile.mkdtemp()

    # Initialize a new Git repository in the temporary directory
    Repo.init(repo_dir)

    # Change the current working directory to the temporary directory
    prev_cwd = os.getcwd()
    os.chdir(repo_dir)

    # Add a cleanup function to remove the temporary directory after the test
    def cleanup():
        os.chdir(prev_cwd)
        shutil.rmtree(repo_dir)

    request.addfinalizer(cleanup)

    return repo_dir
