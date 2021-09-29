import os
import subprocess

import pytest


@pytest.mark.parametrize(
    "filename",
    [
        "base-with-nbs-pys.yml",
        "base-with-nbs.yml",
        "base-with-pys.yml",
        "base-without-nbs.yml",
        "material-with-nbs-pys.yml",
        "material-with-nbs.yml",
        "material-with-pys.yml",
    ],
)
def test_can_render_notebook(filename):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    mkdocs_dir = os.path.join(this_dir, "mkdocs")

    run = subprocess.run(
        ["mkdocs", "build", "-q", "-f", f"{filename}"], cwd=mkdocs_dir
    )
    assert run.returncode == 0
