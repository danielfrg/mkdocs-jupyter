import pytest 
import subprocess

@pytest.mark.parametrize("filename", ["mkdocs-basic", "mkdocs-jupyter"])
def test_can_render_notebook(filename):
    run = subprocess.run(["mkdocs", "build", "-f",  f"tests/{filename}.yml"])
    assert run.returncode == 0
