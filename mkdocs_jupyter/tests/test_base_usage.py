import os
import subprocess

import pytest


@pytest.mark.parametrize("filename", ["mkdocs-without-nbs", "mkdocs-with-nbs"])
def test_can_render_notebook(filename):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    fpath = os.path.join(this_dir, f"{filename}.yml")
    run = subprocess.run(["mkdocs", "build", "-q", "-f", fpath])
    assert run.returncode == 0
