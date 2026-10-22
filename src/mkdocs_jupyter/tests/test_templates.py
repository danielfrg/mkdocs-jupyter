import base64
import json

import jupytext
import nbformat
import pytest
import yaml
from bs4 import BeautifulSoup
from jinja2 import TemplateNotFound
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort


CHILD_TEMPLATE = """{% extends "mkdocs_html/notebook.html.j2" %}
{% block extra_css %}{{ resources.include_css("custom.css") }}{% endblock %}
{% block output_group %}
<details class="custom-output"><summary>
{% set summary = "partials/summary.html.j2" %}{% include summary %}
</summary>{{ super() }}</details>
{% endblock output_group %}
"""


@pytest.fixture
def template_site(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / "docs").mkdir(parents=True)
    (project / "overrides/partials").mkdir(parents=True)
    # This filename also exists in nbconvert's lab template directory.
    (project / "overrides/index.html.j2").write_text(CHILD_TEMPLATE, encoding="utf-8")
    (project / "overrides/partials/summary.html.j2").write_text(
        "Show output", encoding="utf-8"
    )
    (project / "overrides/custom.css").write_text(
        ".custom-output { color: red; }", encoding="utf-8"
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    return project


def write_template_notebook(project, fmt="ipynb", suffix=".ipynb"):
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell("# Notebook title\n\n## Real section"),
            nbformat.v4.new_code_cell(
                "print('template output')",
                execution_count=7,
                outputs=[
                    nbformat.v4.new_output(
                        "stream", name="stdout", text="template output\n"
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
    jupytext.write(notebook, project / "docs" / f"notebook{suffix}", fmt=fmt)


def build_template_site(project, **options):
    config_file = project / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Custom notebook templates",
                "theme": {"name": "material"},
                "plugins": [
                    {
                        "mkdocs-jupyter": {
                            "custom_template": "overrides/index.html.j2",
                            "cache_dir": str(project / ".cache"),
                            **options,
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(str(config_file)))
    return BeautifulSoup(
        (project / "site/notebook/index.html").read_text(encoding="utf-8"),
        "html.parser",
    )


@pytest.mark.parametrize(
    "fmt,suffix", [("ipynb", ".ipynb"), ("py:percent", ".py"), ("md", ".md")]
)
def test_custom_child_template_preserves_notebook_rendering_and_options(
    template_site, fmt, suffix
):
    write_template_notebook(template_site, fmt, suffix)
    html = build_template_site(
        template_site,
        execute=True,
        no_prompt=True,
        highlight_extra_classes="custom-cell",
        custom_mathjax_url="/custom-mathjax.js",
    )
    output = html.select_one(".jupyter-wrapper details.custom-output")
    assert output is not None
    assert output.summary.get_text(strip=True) == "Show output"
    assert "template output" in output.get_text()
    assert html.select_one(".custom-cell") is not None
    assert not html.select(".jp-InputPrompt, .jp-OutputPrompt")
    bootstrap = html.select_one("script[data-mkdocs-jupyter-mathjax]")
    assert bootstrap is not None
    assert json.loads(bootstrap["data-mkdocs-jupyter-mathjax"]) == {
        "url": "/custom-mathjax.js",
        "version": 4,
    }
    assert ".custom-output { color: red; }" in "".join(
        style.get_text() for style in html.select("style")
    )
    assert html.select_one('.md-nav--secondary a[href="#real-section"]') is not None
    assert html.select_one(".jupyter-wrapper h1")["id"] == "notebook-title"


def test_custom_template_and_included_asset_edits_take_effect_with_cache_enabled(
    template_site,
):
    write_template_notebook(template_site)
    first = build_template_site(template_site)
    assert (
        first.select_one("details.custom-output summary").get_text(strip=True)
        == "Show output"
    )

    (template_site / "overrides/partials/summary.html.j2").write_text(
        "Updated summary", encoding="utf-8"
    )
    (template_site / "overrides/custom.css").write_text(
        ".custom-output { color: blue; }", encoding="utf-8"
    )
    second = build_template_site(template_site)
    assert (
        second.select_one("details.custom-output summary").get_text(strip=True)
        == "Updated summary"
    )
    assert ".custom-output { color: blue; }" in "".join(
        style.get_text() for style in second.select("style")
    )

    path = template_site / "overrides/index.html.j2"
    path.write_text(
        CHILD_TEMPLATE.replace('class="custom-output"', 'class="revised-output"'),
        encoding="utf-8",
    )
    third = build_template_site(template_site)
    assert third.select_one("details.revised-output") is not None


@pytest.mark.parametrize("path", ["overrides/missing.html.j2", "overrides"])
def test_custom_template_must_be_an_existing_file(template_site, caplog, path):
    write_template_notebook(template_site)
    with pytest.raises(Abort):
        build_template_site(template_site, custom_template=path)
    assert "custom_template" in caplog.text
    assert str(template_site / path) in caplog.text


def test_missing_custom_partial_is_not_hidden_by_a_previous_cached_build(template_site):
    write_template_notebook(template_site)
    build_template_site(template_site)
    (template_site / "overrides/partials/summary.html.j2").unlink()
    with pytest.raises(TemplateNotFound, match="partials/summary.html.j2"):
        build_template_site(template_site)


def test_custom_template_can_embed_a_binary_asset(template_site):
    write_template_notebook(template_site)
    image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jL9sAAAAASUVORK5CYII="
    )
    (template_site / "overrides/image.png").write_bytes(image)
    path = template_site / "overrides/index.html.j2"
    path.write_text(
        CHILD_TEMPLATE.replace(
            "{{ super() }}",
            '<img class="custom-image" src="{{ resources.include_url("image.png") }}">'
            "{{ super() }}",
        ),
        encoding="utf-8",
    )
    html = build_template_site(template_site)
    source = html.select_one("img.custom-image")["src"]
    assert source.startswith("data:image/png;base64,")
    assert base64.b64decode(source.split(",", 1)[1]) == image
