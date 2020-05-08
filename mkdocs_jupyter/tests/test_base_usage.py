import os
import subprocess

import pytest


@pytest.mark.parametrize("filename", ["mkdocs-without-nbs.yml", "mkdocs-with-nbs.yml"])
def test_can_render_notebook(filename):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    mkdocs_dir = os.path.join(this_dir, "mkdocs")

    run = subprocess.run(["mkdocs", "build", "-q", "-f", f"{filename}"], cwd=mkdocs_dir)
    assert run.returncode == 0
