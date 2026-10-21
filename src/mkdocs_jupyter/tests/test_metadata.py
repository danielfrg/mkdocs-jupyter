import copy
import json
from unittest.mock import patch

import jupytext
import nbformat
import pytest
import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import ConfigurationError
from mkdocs.plugins import BasePlugin

from mkdocs_jupyter import convert


class PageObserver(BasePlugin):
    def __init__(self):
        self.markdown_meta = {}
        self.pages = {}

    def on_page_markdown(self, markdown, page, config, files):
        self.markdown_meta[page.file.src_uri] = copy.deepcopy(page.meta)

    def on_page_content(self, html, page, config, files):
        self.pages[page.file.src_uri] = page


@pytest.fixture
def metadata_site(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        "# Home\n\nPublic searchable page.", encoding="utf-8"
    )
    return tmp_path


def write_notebook(root, filename, cells):
    notebook = nbformat.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "name": "python3",
                "language": "python",
                "display_name": "Python 3",
            }
        },
    )
    path = root / "docs" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".ipynb":
        nbformat.write(notebook, path)
    else:
        jupytext.write(
            notebook, path, fmt="py:percent" if path.suffix == ".py" else "md"
        )
    return path


def build_metadata_site(root, options=None, nav=None):
    settings = {
        "site_name": "Notebook metadata",
        "theme": {"name": "material"},
        "plugins": ["material/search", {"mkdocs-jupyter": options or {}}],
    }
    if nav is not None:
        settings["nav"] = nav
    config_file = root / "mkdocs.yml"
    config_file.write_text(yaml.safe_dump(settings), encoding="utf-8")
    config = load_config(str(config_file))
    observer = PageObserver()
    config.plugins["page-observer"] = observer
    config.plugins.run_event("startup", command="build", dirty=False)
    try:
        build(config)
    finally:
        config.plugins.run_event("shutdown")
    return observer


def read_page(root, name):
    return BeautifulSoup(
        (root / "site" / name / "index.html").read_text(encoding="utf-8"),
        "html.parser",
    )


def toc_titles(toc):
    return [title for item in toc for title in [item.title, *toc_titles(item.children)]]


def read_search_docs(root):
    return json.loads(
        (root / "site/search/search_index.json").read_text(encoding="utf-8")
    )["docs"]


@pytest.mark.parametrize("extension", ["ipynb", "py", "md"])
def test_metadata_reaches_page_hooks_material_and_warm_cache(metadata_site, extension):
    metadata = {
        "title": "Metadata page title",
        "description": "A private notebook description.",
        "hide": ["navigation", "toc"],
        "search": {"exclude": True},
        "custom": {"owner": "Notebook author", "labels": ["example", "private"]},
    }
    source = write_notebook(
        metadata_site,
        f"notebook.{extension}",
        [
            nbformat.v4.new_code_cell("value = 42"),
            nbformat.v4.new_markdown_cell(
                "---\n"
                + yaml.safe_dump(metadata)
                + "---\n\n# Actual heading\n\nNotebook body.\n\n"
                "## Details\n\nMore content."
            ),
        ],
    )
    original_source = source.read_bytes()
    options = {"include_source": True}

    with patch("mkdocs_jupyter.convert.nb2html", wraps=convert.nb2html) as renderer:
        cold = build_metadata_site(metadata_site, options)
        assert renderer.call_count == 1
        cold_html = read_page(metadata_site, "notebook")
        cold_search = read_search_docs(metadata_site)
        renderer.reset_mock()
        warm = build_metadata_site(metadata_site, options)
        renderer.assert_not_called()

    for observer, html, search_docs in (
        (cold, cold_html, cold_search),
        (warm, read_page(metadata_site, "notebook"), read_search_docs(metadata_site)),
    ):
        assert observer.markdown_meta[source.name] == metadata
        page = observer.pages[source.name]
        assert page.meta == metadata
        assert page.title == "Metadata page title"
        assert toc_titles(page.toc) == ["Actual heading", "Details"]
        rendered = BeautifulSoup(page.content, "html.parser")
        body = rendered.select_one(".jupyter-wrapper")
        assert "Notebook body." in body.get_text()
        assert "Metadata page title" not in body.get_text()
        assert "Notebook author" not in body.get_text()
        assert [heading["id"] for heading in body.select("h1, h2")] == [
            "actual-heading",
            "details",
        ]

        assert html.title.get_text() == "Metadata page title - Notebook metadata"
        assert html.find("meta", attrs={"name": "description"})["content"] == metadata[
            "description"
        ]
        assert html.select_one(".md-sidebar--primary").has_attr("hidden")
        assert html.select_one(".md-sidebar--secondary").has_attr("hidden")
        assert any("Public searchable page" in entry["text"] for entry in search_docs)
        assert not any(
            entry["location"].startswith("notebook/") for entry in search_docs
        )
    assert source.read_bytes() == original_source
    copied_source = metadata_site / "site/notebook" / source.name
    assert copied_source.read_bytes() == original_source


def test_metadata_title_precedence_preserves_legacy_notebooks(metadata_site):
    sources = {
        "navigation": "---\ntitle: Metadata title\n---\n\n# Heading title",
        "metadata": "---\ntitle: Metadata title\n---\n\n# Heading title",
        "heading": "---\ncustom: value\n---\n\n# Heading title",
        "fallback": "---\ncustom: value\n---\n\nNotebook without a heading.",
        "empty": "---\n{}\n---\n\n# Empty mapping heading",
        "legacy": "# Legacy heading\n\nExisting notebook behavior.",
    }
    for name, markdown in sources.items():
        write_notebook(
            metadata_site, f"{name}.ipynb", [nbformat.v4.new_markdown_cell(markdown)]
        )
    write_notebook(
        metadata_site,
        "header-only.ipynb",
        [
            nbformat.v4.new_markdown_cell("---\ntitle: Header-only title\n---"),
            nbformat.v4.new_markdown_cell("# Header-only body\n\nSeparate body cell."),
        ],
    )
    nav = [
        {"Home": "index.md"},
        {"Navigation title": "navigation.ipynb"},
        "metadata.ipynb",
        "heading.ipynb",
        "fallback.ipynb",
        {"Empty mapping navigation": "empty.ipynb"},
        "header-only.ipynb",
        {"Legacy navigation title": "legacy.ipynb"},
    ]
    expected_titles = {
        "navigation": "Navigation title",
        "metadata": "Metadata title",
        "heading": "Heading title",
        "fallback": "Fallback",
        "empty": "Empty mapping navigation",
        "header-only": "Header-only title",
        "legacy": "Legacy heading",
    }
    build_metadata_site(metadata_site, nav=nav)
    with patch("mkdocs_jupyter.convert.nb2html") as renderer:
        observer = build_metadata_site(metadata_site, nav=nav)
        renderer.assert_not_called()
    for name, expected_title in expected_titles.items():
        page = observer.pages[f"{name}.ipynb"]
        assert page.title == expected_title
        html = read_page(metadata_site, name)
        active_link = html.select_one(".md-nav--primary a.md-nav__link--active")
        assert active_link.get_text(" ", strip=True) == expected_title
        # Material deliberately uses meta.title for the browser tab title.
        html_title = page.meta.get("title", expected_title)
        assert html.title.get_text() == f"{html_title} - Notebook metadata"
    empty = observer.pages["empty.ipynb"]
    assert empty.meta == {}
    assert toc_titles(empty.toc) == ["Empty mapping heading"]
    assert "{}" not in BeautifulSoup(empty.content, "html.parser").get_text()
    header_only = observer.pages["header-only.ipynb"]
    assert header_only.meta == {"title": "Header-only title"}
    assert toc_titles(header_only.toc) == ["Header-only body"]
    assert "Separate body cell." in header_only.content
    legacy = observer.pages["legacy.ipynb"]
    assert legacy.meta == {}
    assert "Existing notebook behavior." in legacy.content
    assert toc_titles(legacy.toc) == ["Legacy heading"]


def test_later_cell_and_fenced_yaml_remain_notebook_content(metadata_site):
    write_notebook(
        metadata_site,
        "later.ipynb",
        [
            nbformat.v4.new_markdown_cell("# First heading\n\nOrdinary first cell."),
            nbformat.v4.new_markdown_cell(
                "---\ntitle: Later cell metadata\n---\n\n## Later heading"
            ),
        ],
    )
    write_notebook(
        metadata_site,
        "fenced.ipynb",
        [
            nbformat.v4.new_markdown_cell(
                "```yaml\n---\ntitle: Fenced metadata example\n---\n```\n\n"
                "# Fenced heading"
            )
        ],
    )
    observer = build_metadata_site(metadata_site)
    for name, literal_title in (
        ("later", "Later cell metadata"),
        ("fenced", "Fenced metadata example"),
    ):
        assert observer.markdown_meta[f"{name}.ipynb"] == {}
        body = read_page(metadata_site, name).select_one(".jupyter-wrapper")
        assert literal_title in body.get_text()
    assert toc_titles(observer.pages["fenced.ipynb"].toc) == ["Fenced heading"]


def test_metadata_precedes_cell_removal_and_respects_ignored_h1(metadata_site):
    write_notebook(
        metadata_site,
        "ordering.ipynb",
        [
            nbformat.v4.new_markdown_cell(
                "---\ncustom: kept\n---\n\n# Removed heading\n\nRemoved cell body.",
                metadata={"tags": ["remove"]},
            ),
            nbformat.v4.new_markdown_cell(
                "---\ntitle: Literal later YAML\n---\n\n"
                "# Body heading\n\nRetained body."
            ),
        ],
    )
    observer = build_metadata_site(
        metadata_site,
        {
            "ignore_h1_titles": True,
            "remove_tag_config": {"remove_cell_tags": ["remove"]},
        },
    )
    page = observer.pages["ordering.ipynb"]
    assert observer.markdown_meta["ordering.ipynb"] == {"custom": "kept"}
    assert page.title == "Ordering"
    body = read_page(metadata_site, "ordering").select_one(".jupyter-wrapper")
    assert "Removed cell body." not in body.get_text()
    assert "Literal later YAML" in body.get_text()
    assert "Retained body." in body.get_text()


@pytest.mark.parametrize("extension", ["ipynb", "py", "md"])
@pytest.mark.parametrize(
    "markdown",
    [
        "---\ntitle: [unfinished\n---\n\n# Body",
        "---\ntitle: Unclosed metadata\n\n# Body",
        "---\n- a list is not page metadata\n---\n\n# Body",
    ],
    ids=["invalid-yaml", "unclosed-frontmatter", "nonmapping-frontmatter"],
)
def test_invalid_metadata_reports_source_file(metadata_site, extension, markdown):
    source = write_notebook(
        metadata_site,
        f"examples/invalid.{extension}",
        [nbformat.v4.new_markdown_cell(markdown)],
    )
    original_source = source.read_bytes()
    with pytest.raises(ConfigurationError, match=rf"examples[/\\]invalid\.{extension}"):
        build_metadata_site(metadata_site)
    assert source.read_bytes() == original_source
