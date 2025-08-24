import os
from unittest.mock import patch

import pytest
from mkdocs.structure.files import File

import mkdocs_jupyter
from mkdocs_jupyter import plugin
from mkdocs_jupyter.config import settings

pytestmark = [pytest.mark.pkg]


def test_import():
    assert mkdocs_jupyter.__version__ is not None
    assert mkdocs_jupyter.__version__ != "0.0.0"
    assert len(mkdocs_jupyter.__version__) > 0


def test_assets_included():
    mkdocs_html = os.path.join(settings.templates_dir, "mkdocs_html")
    assert os.path.exists(os.path.join(mkdocs_html, "conf.json"))
    assert os.path.exists(os.path.join(mkdocs_html, "notebook.html.j2"))

    html_assets = os.path.join(mkdocs_html, "assets")
    assert os.path.exists(os.path.join(html_assets, "clipboard.umd.js"))
    assert os.path.exists(os.path.join(html_assets, "index.css"))
    assert os.path.exists(os.path.join(html_assets, "theme-dark.css"))
    assert os.path.exists(os.path.join(html_assets, "theme-light.css"))

    mkdocs_md = os.path.join(settings.templates_dir, "mkdocs_md")
    assert os.path.exists(os.path.join(mkdocs_md, "conf.json"))
    assert os.path.exists(os.path.join(mkdocs_md, "md-no-codecell.md.j2"))


def test_markdown_ignored_without_parsing() -> None:
    """
    Test that ignored Markdown files are not parsed.
    """
    plug = plugin.Plugin()
    plug.config["ignore"] = ["**/*.md"]
    dummy_md_file = File("file.md", "docs", "site", False)
    with patch.object(plugin.jupytext, "read") as mock_read:
        assert plug.should_include(dummy_md_file) is False
        assert mock_read.call_count == 0
