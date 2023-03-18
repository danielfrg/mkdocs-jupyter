import os

import pytest
from mkdocs.commands.build import build
from mkdocs.config import load_config
from nbclient.exceptions import CellExecutionError


@pytest.mark.parametrize(
    "input",
    [
        ["base-with-nbs-pys.yml", True],
        ["base-with-nbs.yml", True],
        ["base-with-pys.yml", True],
        ["base-without-nbs.yml", True],
        ["material-execute-ignore.yml", True],
        ["material-with-nbs-pys.yml", True],
        ["material-with-nbs.yml", True],
        ["material-with-pys.yml", True],
        ["base-with-nbs-failure.yml", False],
    ],
)
def test_notebook_renders(input):
    filename, should_work = input

    this_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(this_dir, f"mkdocs/{filename}")

    try:
        build(load_config(config_file))
        assert should_work
    except CellExecutionError:
        assert not should_work
