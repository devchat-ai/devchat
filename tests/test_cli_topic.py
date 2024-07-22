import json
import sys
import time

import pytest
from click.testing import CliRunner

from devchat._cli.main import main
from devchat.utils import get_prompt_hash

runner = CliRunner()


@pytest.mark.skip(reason="No working as expected. However, the cli is outdated and not necessary.")
def test_topic_list(git_repo):
    request = "Complete the sequence 1, 1, 3, 5, 9, ( ). Reply the number only."
    sys.argv = ["prompt", "--model=gpt-3.5-turbo", request]
    result = runner.invoke(main, ["prompt", "--model=gpt-3.5-turbo", request])
    assert result.exit_code == 0
    topic1 = get_prompt_hash(result.output)

    time.sleep(3)

    result = runner.invoke(main, ["prompt", "--model=gpt-4", request])
    assert result.exit_code == 0
    topic2 = get_prompt_hash(result.output)

    result = runner.invoke(main, ["topic", "--list"])
    assert result.exit_code == 0
    topics = json.loads(result.output)
    assert len(topics) >= 2
    assert topics[0]["root_prompt"]["responses"][0] == "15"
    assert topics[1]["root_prompt"]["responses"][0] == "17"
    assert topics[0]["root_prompt"]["hash"] == topic2
    assert topics[1]["root_prompt"]["hash"] == topic1
