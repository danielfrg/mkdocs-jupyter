"""Exercise notebook Markdown through a real MkDocs/mkdocstrings build."""

import base64
from unittest.mock import patch

import jupytext
import nbformat
import pytest
import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config


FORMATS = [("ipynb", ".ipynb"), ("py:percent", ".py"), ("md", ".md")]
REFERENCE = "[`Target.fit`][mkdocs236_fixture.Target.fit]"


@pytest.fixture
def markdown_site(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / "docs/notebooks").mkdir(parents=True)
    (project / "mkdocs236_fixture.py").write_text(
        "class Target:\n"
        '    """A documented API class."""\n\n'
        "    def fit(self, value: int) -> int:\n"
        '        """Return the supplied value."""\n'
        "        return value\n",
        encoding="utf-8",
    )
    (project / "docs/api.md").write_text(
        "# API reference\n\n::: mkdocs236_fixture.Target\n", encoding="utf-8"
    )
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    return project


def write_notebook(project, cells, *, name="example", fmt="ipynb", suffix=".ipynb"):
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
    source = project / "docs/notebooks" / f"{name}{suffix}"
    jupytext.write(notebook, source, fmt=fmt)
    return source


def build_site(
    project, *, suffix=".ipynb", api_name="api", extensions=None, nav=None, **options
):
    config_path = project / "mkdocs.yml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "site_name": "Notebook Markdown integration",
                "theme": {"name": "material"},
                # Put the referencing notebook before the API target intentionally.
                "nav": nav
                if nav is not None
                else [
                    {"Notebook": f"notebooks/example{suffix}"},
                    {"API": f"{api_name}.md"},
                ],
                "plugins": [
                    {
                        "mkdocs-jupyter": {
                            "cache_dir": str(project / ".cache"),
                            **options,
                        }
                    },
                    "autorefs",
                    {
                        "mkdocstrings": {
                            "handlers": {
                                "python": {
                                    "paths": [str(project)],
                                    "options": {
                                        "show_root_heading": True,
                                        "show_source": False,
                                    },
                                }
                            }
                        }
                    },
                ],
                "markdown_extensions": extensions or ["attr_list", "admonition"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    config = load_config(str(config_path))
    build(config)
    html = BeautifulSoup(
        (project / "site/notebooks/example/index.html").read_text(encoding="utf-8"),
        "html.parser",
    )
    return html, config


def api_link(html):
    return html.select_one('a[href$="#mkdocs236_fixture.Target.fit"]')


def require_node(html, selector):
    node = html.select_one(selector)
    assert node is not None, f"Missing rendered node: {selector}"
    return node


@pytest.mark.parametrize("fmt,suffix", FORMATS)
def test_mkdocs_processor_resolves_api_references_and_configured_markdown(
    markdown_site, fmt, suffix
):
    write_notebook(
        markdown_site,
        [
            nbformat.v4.new_markdown_cell(
                "# Notebook title {#notebook-custom}\n\n"
                + REFERENCE
                + "\n\n## A custom section {#section-custom}\n\n"
                '!!! note "Pipeline note"\n'
                "    **Configured admonition**\n\n"
                "[Sibling notebook](sibling.ipynb#sibling-custom)\n\n"
                r"Inline $x^2$ and display:"
                "\n\n$$y^2$$"
            )
        ],
        fmt=fmt,
        suffix=suffix,
    )
    write_notebook(
        markdown_site,
        [nbformat.v4.new_markdown_cell("# Sibling {#sibling-custom}")],
        name="sibling",
    )
    html, _ = build_site(
        markdown_site,
        suffix=suffix,
        markdown_cell_processor="mkdocs",
        extensions=[
            "attr_list",
            "admonition",
            {"pymdownx.arithmatex": {"generic": True}},
        ],
    )
    reference = api_link(html)
    assert reference is not None
    assert reference["href"] == "../../api/#mkdocs236_fixture.Target.fit"
    assert reference.get_text() == "Target.fit"
    require_node(html, ".jupyter-wrapper h1#notebook-custom")
    require_node(html, ".jupyter-wrapper h2#section-custom")
    require_node(html, '.md-nav--secondary a[href="#section-custom"]')
    assert require_node(
        html, ".jupyter-wrapper .admonition.note strong"
    ).get_text() == ("Configured admonition")
    sibling = html.find("a", string="Sibling notebook")
    assert sibling["href"] == "../sibling/#sibling-custom"
    assert len(html.select(".jupyter-wrapper .arithmatex")) == 2
    assert not html.select("[markdown]")


@pytest.mark.parametrize("options", [{}, {"markdown_cell_processor": "jupyter"}])
def test_jupyter_processor_remains_the_default(markdown_site, options):
    write_notebook(
        markdown_site,
        [
            nbformat.v4.new_markdown_cell(
                "# Default title\n\n" + REFERENCE + '\n\n!!! note "No conversion"'
            )
        ],
    )
    html, _ = build_site(markdown_site, **options)
    require_node(html, ".jupyter-wrapper h1#default-title")
    assert api_link(html) is None
    assert (
        "[mkdocs236_fixture.Target.fit]"
        in html.select_one(".jupyter-wrapper").get_text()
    )
    assert html.select_one(".jupyter-wrapper .admonition") is None


def test_mkdocs_processor_keeps_cell_attachments_and_outputs_separate(markdown_site):
    first = base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg"><text>one</text></svg>'
    ).decode()
    second = base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg"><text>two</text></svg>'
    ).decode()
    literal_code = (
        '# Literal code heading\nprint("[Target.fit][mkdocs236_fixture.Target.fit]")'
    )
    literal_output = (
        "# Literal output heading\n[Target.fit][mkdocs236_fixture.Target.fit]\n"
    )
    write_notebook(
        markdown_site,
        [
            nbformat.v4.new_markdown_cell(
                "# Attachments\n\n![first image](attachment:image.svg)",
                attachments={"image.svg": {"image/svg+xml": first}},
            ),
            nbformat.v4.new_code_cell(
                literal_code,
                execution_count=1,
                outputs=[
                    nbformat.v4.new_output(
                        "stream", name="stdout", text=literal_output
                    ),
                    nbformat.v4.new_output(
                        "display_data",
                        data={
                            "text/html": (
                                '<div class="raw-output">**literal output** '
                                "[Target.fit][mkdocs236_fixture.Target.fit]</div>"
                            )
                        },
                    ),
                    nbformat.v4.new_output(
                        "display_data", data={"text/latex": "$$x+y$$"}
                    ),
                ],
            ),
            nbformat.v4.new_markdown_cell(
                "![second image][picture]\n\n[picture]: attachment:image.svg",
                attachments={"image.svg": {"image/svg+xml": second}},
            ),
        ],
    )
    html, _ = build_site(markdown_site, markdown_cell_processor="mkdocs")
    assert (
        html.find("img", alt="first image")["src"]
        == f"data:image/svg+xml;base64,{first}"
    )
    assert (
        html.find("img", alt="second image")["src"]
        == f"data:image/svg+xml;base64,{second}"
    )
    assert (
        literal_code in html.select_one(".jp-CodeCell .jp-InputArea-editor").get_text()
    )
    assert literal_output in html.select_one(".jp-OutputArea").get_text()
    output = html.select_one(".raw-output")
    assert output.get_text().startswith("**literal output**")
    assert output.find("strong") is None
    assert output.find("a") is None
    require_node(html, '[data-mime-type="text/latex"] .arithmatex')
    assert html.select_one("h1#literal-code-heading") is None
    assert html.select_one("h1#literal-output-heading") is None


def test_warm_cache_rerenders_references_and_does_not_mix_processor_modes(
    markdown_site,
):
    write_notebook(
        markdown_site,
        [nbformat.v4.new_markdown_cell("# Cached notebook\n\n" + REFERENCE)],
    )
    first, _ = build_site(markdown_site, markdown_cell_processor="mkdocs")
    first_link = api_link(first)
    assert first_link is not None
    assert first_link["href"] == "../../api/#mkdocs236_fixture.Target.fit"
    assert list((markdown_site / ".cache").glob("*.json"))

    (markdown_site / "docs/api.md").rename(markdown_site / "docs/renamed-api.md")
    with patch(
        "mkdocs_jupyter.plugin.convert.nb2html",
        side_effect=AssertionError("Warm build must reuse the notebook conversion"),
    ):
        second, _ = build_site(
            markdown_site,
            markdown_cell_processor="mkdocs",
            api_name="renamed-api",
        )
    second_link = api_link(second)
    assert second_link is not None
    assert second_link["href"] == "../../renamed-api/#mkdocs236_fixture.Target.fit"

    default, _ = build_site(markdown_site, api_name="renamed-api")
    assert api_link(default) is None
    assert (
        "[mkdocs236_fixture.Target.fit]"
        in default.select_one(".jupyter-wrapper").get_text()
    )


def test_mkdocs_processor_preserves_page_metadata_and_notebook_toc_depth(markdown_site):
    write_notebook(
        markdown_site,
        [
            nbformat.v4.new_markdown_cell(
                "---\ntitle: Metadata title\ncustom_value: retained\n---\n"
                "# Rendered heading {#metadata-heading}\n\n"
                "## Visible section {#visible-section}\n\n"
                "### Deep section {#deep-section}"
            )
        ],
    )
    html, _ = build_site(
        markdown_site,
        markdown_cell_processor="mkdocs",
        ignore_h1_titles=True,
        toc_depth=2,
    )
    require_node(html, ".jupyter-wrapper h1#metadata-heading")
    require_node(html, '.md-nav--secondary a[href="#visible-section"]')
    assert html.select_one('.md-nav--secondary a[href="#deep-section"]') is None
    assert "title: Metadata title" not in html.select_one(".jupyter-wrapper").get_text()
    assert "Metadata title" in html.title.get_text()


def test_mkdocs_processor_preserves_execution_and_cell_options(
    markdown_site, tmp_path, monkeypatch
):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    (markdown_site / "docs/notebooks/input.txt").write_text(
        "fresh-from-sibling-data", encoding="utf-8"
    )
    write_notebook(
        markdown_site,
        [
            nbformat.v4.new_markdown_cell("# Executed notebook\n\n" + REFERENCE),
            nbformat.v4.new_code_cell(
                "from pathlib import Path\nprint(Path('input.txt').read_text())",
                execution_count=1,
                outputs=[
                    nbformat.v4.new_output(
                        "stream", name="stdout", text="stale-saved-output\n"
                    )
                ],
            ),
            nbformat.v4.new_markdown_cell(
                "## Removed heading {#removed-heading}",
                metadata={"tags": ["remove-this-cell"]},
            ),
        ],
    )
    html, _ = build_site(
        markdown_site,
        markdown_cell_processor="mkdocs",
        execute=True,
        show_input=False,
        no_prompt=True,
        remove_tag_config={"remove_cell_tags": ["remove-this-cell"]},
    )
    reference = api_link(html)
    assert reference is not None
    assert reference["href"] == "../../api/#mkdocs236_fixture.Target.fit"
    output = require_node(html, ".jupyter-wrapper .jp-OutputArea-output").get_text()
    assert "fresh-from-sibling-data" in output
    assert "stale-saved-output" not in output
    inputs = html.select(".jp-CodeCell .jp-InputArea")
    prompts = html.select(".jp-InputPrompt, .jp-OutputPrompt")
    assert not inputs
    assert not prompts
    assert "Removed heading" not in html.select_one(".jupyter-wrapper").get_text()
    assert not html.select('a[href="#removed-heading"]')


@pytest.mark.parametrize(
    "ignore_h1_titles,nav_title,metadata_title,expected_title",
    [
        (False, None, None, "An emphasized H1"),
        (True, None, None, "Example"),
        (False, "Explicit navigation title", None, "Explicit navigation title"),
        (False, None, "Explicit metadata title", "Explicit metadata title"),
    ],
)
def test_mkdocs_processor_derives_title_from_rendered_h1_with_title_overrides(
    markdown_site, ignore_h1_titles, nav_title, metadata_title, expected_title
):
    source = "# An *emphasized* `H1` {#formatted-heading}"
    if metadata_title:
        source = f"---\ntitle: {metadata_title}\n---\n" + source
    write_notebook(markdown_site, [nbformat.v4.new_markdown_cell(source)])
    notebook_nav = (
        {nav_title: "notebooks/example.ipynb"}
        if nav_title
        else "notebooks/example.ipynb"
    )
    html, _ = build_site(
        markdown_site,
        nav=[notebook_nav, "api.md"],
        markdown_cell_processor="mkdocs",
        ignore_h1_titles=ignore_h1_titles,
    )
    heading = require_node(html, ".jupyter-wrapper h1#formatted-heading")
    assert heading.get_text() == "An emphasized H1"
    title = html.title.get_text()
    assert title == f"{expected_title} - Notebook Markdown integration"


def test_mkdocs_processor_embeds_images_without_rewriting_literal_attachment_urls(
    markdown_site,
):
    image = base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg"><text>attachment</text></svg>'
    ).decode()
    write_notebook(
        markdown_site,
        [
            nbformat.v4.new_markdown_cell(
                "# Attachment examples\n\n"
                "![actual attachment](attachment:fixture.svg)\n\n"
                "Inline code: `attachment:fixture.svg`.\n\n"
                "The attachment URL is attachment:fixture.svg.\n\n"
                "```markdown\n![fenced example](attachment:fixture.svg)\n```\n",
                attachments={"fixture.svg": {"image/svg+xml": image}},
            )
        ],
    )
    html, _ = build_site(markdown_site, markdown_cell_processor="mkdocs")
    embedded = html.find("img", alt="actual attachment")
    assert embedded is not None
    assert embedded["src"] == f"data:image/svg+xml;base64,{image}"
    notebook = require_node(html, ".jupyter-wrapper")
    examples = [node.get_text() for node in notebook.find_all("code")]
    assert "attachment:fixture.svg" in examples
    assert any("![fenced example](attachment:fixture.svg)" in code for code in examples)
    assert "The attachment URL is attachment:fixture.svg." in notebook.get_text()
