import jupytext
import nbformat
import pytest
import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config

from mkdocs_jupyter import convert


DIAGRAM = 'graph TD\n    A["Notebook & diagram"] --> B[Rendered]'


def write_mermaid_notebook(path, fmt="ipynb"):
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell(
                "# Diagrams\n\n```mermaid\n" + DIAGRAM + "\n```\n\n"
                "```python\nprint('ordinary code')\n```"
            ),
            nbformat.v4.new_code_cell(
                "# Saved Mermaid output",
                outputs=[
                    nbformat.v4.new_output(
                        "display_data",
                        data={"text/vnd.mermaid": DIAGRAM, "text/plain": "Diagram"},
                    )
                ],
            ),
        ],
        metadata={
            "kernelspec": {
                "name": "python3",
                "language": "python",
                "display_name": "Python 3",
            }
        },
    )
    jupytext.write(notebook, path, fmt=fmt)


def build_mermaid_site(root, theme):
    config_file = root / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Mermaid notebooks",
                "theme": {"name": theme},
                "plugins": [
                    {
                        "mkdocs-jupyter": {
                            "cache_dir": str(root / ".cache" / "notebooks")
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(str(config_file)))
    return BeautifulSoup(
        (root / "site/diagram/index.html").read_text(encoding="utf-8"), "html.parser"
    )


def assert_mermaid_renderer(html, native):
    assert (
        any(
            ".jp-Mermaid > pre.mermaid" in script.get_text()
            for script in html.select('script[type="module"]')
        )
        is native
    )
    assert (
        any(
            ".jp-Mermaid:not(.jp-RenderedMermaid)" in style.get_text()
            for style in html.select("style")
        )
        is native
    )
    assert html.select_one("pre.mermaid").get_text().strip() == DIAGRAM


@pytest.mark.parametrize("theme,native", [("material", False), ("mkdocs", True)])
@pytest.mark.parametrize(
    "fmt,suffix", [("ipynb", ".ipynb"), ("py:percent", ".py"), ("md", ".md")]
)
def test_mermaid_uses_one_renderer_on_cold_and_warm_builds(
    tmp_path, monkeypatch, theme, native, fmt, suffix
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    (tmp_path / "docs").mkdir()
    write_mermaid_notebook(tmp_path / "docs" / f"diagram{suffix}", fmt)

    for _ in range(2):
        html = build_mermaid_site(tmp_path, theme)
        assert_mermaid_renderer(html, native)
        assert "print('ordinary code')" in html.get_text()
        # Jupytext text formats intentionally do not retain saved cell outputs.
        assert len(html.select("pre.mermaid")) == (2 if suffix == ".ipynb" else 1)


def test_switching_site_theme_does_not_reuse_another_mermaid_renderer(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    (tmp_path / "docs").mkdir()
    write_mermaid_notebook(tmp_path / "docs/diagram.ipynb")

    for theme, native in [("mkdocs", True), ("material", False), ("mkdocs", True)]:
        assert_mermaid_renderer(build_mermaid_site(tmp_path, theme), native)


def test_direct_html_conversion_retains_native_mermaid_renderer(tmp_path):
    path = tmp_path / "diagram.ipynb"
    write_mermaid_notebook(path)
    html = BeautifulSoup(convert.nb2html(str(path)), "html.parser")
    assert_mermaid_renderer(html, True)
