import os
import subprocess

import pytest

CURDIR = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize("filename", ["mkdocs-without-nbs", "mkdocs-with-nbs"])
def test_can_render_notebook(filename):
    fpath = os.path.join(CURDIR, f"{filename}.yml")
    run = subprocess.run(["mkdocs", "build", "-q", "-f", fpath])
    assert run.returncode == 0
