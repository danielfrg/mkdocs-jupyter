"""Public HTMLExporter options work through real notebook conversion and builds."""

import base64
import json

import jupytext
import nbformat
import pytest
import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort, ConfigurationError
from traitlets import TraitError

from mkdocs_jupyter import convert


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jL9sAAAAASUVORK5CYII="
)
MARKDOWN_IMAGE = "![Meaningful Markdown image](assets/plot.png)"
HTML_IMAGE = '<img src="assets/plot.png" alt="Meaningful HTML image" width="123">'


@pytest.fixture
def exporter_site(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / "docs/assets").mkdir(parents=True)
    (project / "docs/assets/plot.png").write_bytes(PNG)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    return project


def write_notebook(project, fmt="ipynb", suffix=".ipynb", markdown=None, code=None):
    if markdown is None:
        markdown = f"# Notebook heading\n\n{MARKDOWN_IMAGE}\n\n{HTML_IMAGE}\n\n$x + 1$"
    if code is None:
        code = "print('saved exporter output')"
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell(markdown),
            nbformat.v4.new_code_cell(
                code,
                execution_count=7,
                outputs=[
                    nbformat.v4.new_output(
                        "stream", name="stdout", text="saved exporter output\n"
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
    path = project / "docs" / f"notebook{suffix}"
    jupytext.write(notebook, path, fmt=fmt)
    return path


def build_exporter_site(project, **options):
    config_file = project / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Notebook exporter options",
                "theme": {"name": "material"},
                "plugins": [
                    {
                        "mkdocs-jupyter": {
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


def embedded_image(html, alt, image=PNG):
    element = html.select_one(f'.jupyter-wrapper img[alt="{alt}"]')
    assert element is not None
    assert element["src"].startswith("data:image/png;base64,")
    assert base64.b64decode(element["src"].split(",", 1)[1]) == image
    return element


@pytest.mark.parametrize(
    "fmt,suffix", [("ipynb", ".ipynb"), ("py:percent", ".py"), ("md", ".md")]
)
def test_exporter_embeds_markdown_and_html_images_in_all_notebook_formats(
    exporter_site, fmt, suffix
):
    write_notebook(exporter_site, fmt, suffix)
    html = build_exporter_site(
        exporter_site, html_exporter_options={"embed_images": True}
    )
    embedded_image(html, "Meaningful Markdown image")
    assert embedded_image(html, "Meaningful HTML image")["width"] == "123"
    assert html.select_one(".jupyter-wrapper .arithmatex").get_text() == r"\(x + 1\)"
    assert "saved exporter output" in html.select_one(".highlight-ipynb").get_text()


def test_direct_api_embeds_images_with_legacy_mathjax(exporter_site):
    notebook = write_notebook(exporter_site)
    html = BeautifulSoup(
        convert.nb2html(
            notebook,
            mathjax_version=2,
            html_exporter_options={"embed_images": True},
        ),
        "html.parser",
    )
    embedded_image(html, "Meaningful Markdown image")
    assert embedded_image(html, "Meaningful HTML image")["width"] == "123"
    assert html.select_one('script[src*="mathjax/2.7.7/"]') is not None


def test_exporter_options_accept_other_configurable_traits(exporter_site):
    write_notebook(exporter_site)
    html = build_exporter_site(
        exporter_site, html_exporter_options={"anchor_link_text": "Section link"}
    )
    assert (
        html.select_one('.jupyter-wrapper h1 a[href="#notebook-heading"]').get_text()
        == "Section link"
    )
    assert html.select_one(".highlight-ipynb") is not None


@pytest.mark.parametrize(
    "options,invalid_name",
    [
        ({"not_an_exporter_trait": True}, "not_an_exporter_trait"),
        ({"enable_async": True}, "enable_async"),
        ({"embed_images": "true"}, "embed_images"),
        ({"anchor_link_text": ["wrong type"]}, "anchor_link_text"),
        (["embed_images"], "html_exporter_options"),
    ],
)
def test_invalid_exporter_options_fail_clearly_before_conversion(
    exporter_site, caplog, options, invalid_name
):
    write_notebook(exporter_site)
    with pytest.raises((Abort, ConfigurationError)) as error:
        build_exporter_site(exporter_site, html_exporter_options=options)
    assert invalid_name in caplog.text + str(error.value)


def test_direct_api_rejects_invalid_exporter_trait_values(exporter_site):
    notebook = write_notebook(exporter_site)
    with pytest.raises((ValueError, TypeError, TraitError), match="embed_images"):
        convert.nb2html(notebook, html_exporter_options={"embed_images": "true"})


@pytest.mark.parametrize(
    "dedicated,generic,input_visible,prompts_visible",
    [
        ({"show_input": False}, {"exclude_input": False}, False, True),
        ({"show_input": True}, {"exclude_input": True}, True, True),
        (
            {"no_input": True},
            {
                "exclude_input": False,
                "exclude_input_prompt": False,
                "exclude_output_prompt": False,
            },
            False,
            False,
        ),
        (
            {"no_prompt": True},
            {"exclude_input_prompt": False, "exclude_output_prompt": False},
            True,
            False,
        ),
    ],
)
def test_dedicated_input_settings_override_conflicting_exporter_options(
    exporter_site, dedicated, generic, input_visible, prompts_visible
):
    notebook = write_notebook(exporter_site)
    # An execute_result has a real output prompt, unlike a stream output.
    contents = nbformat.read(notebook, as_version=4)
    contents.cells[1].outputs = [
        nbformat.v4.new_output(
            "execute_result", execution_count=7, data={"text/plain": "saved result"}
        )
    ]
    nbformat.write(contents, notebook)
    html = build_exporter_site(
        exporter_site, html_exporter_options=generic, **dedicated
    )
    assert bool(html.select(".jp-InputArea-editor")) is input_visible
    assert bool(html.select(".jp-InputPrompt, .jp-OutputPrompt")) is prompts_visible
    assert "saved result" in html.select_one(".jp-OutputArea").get_text()


def test_exporter_options_preserve_package_and_dedicated_renderer_setup(exporter_site):
    notebook = write_notebook(exporter_site)
    template = exporter_site / "custom.html.j2"
    template.write_text(
        '{% extends "mkdocs_html/notebook.html.j2" %}'
        '{% block extra_css %}<span class="custom-template-marker"></span>'
        '{% endblock %}',
        encoding="utf-8",
    )
    html = BeautifulSoup(
        convert.nb2html(
            notebook,
            start=1,
            theme="light",
            custom_template=str(template),
            custom_mathjax_url="/chosen-mathjax.js",
            highlight_extra_classes="chosen-highlight",
            html_exporter_options={
                "template_file": "does-not-exist.html.j2",
                "extra_template_paths": [],
                "filters": {"highlight_code": "builtins.str"},
                "preprocessors": [],
                "theme": "dark",
                "mathjax_url": "/wrong-mathjax.js",
            },
        ),
        "html.parser",
    )
    assert html.select_one(".custom-template-marker") is not None
    assert html.select_one(".jupyter-wrapper h1") is None
    assert html.select_one(".chosen-highlight") is not None
    assert html.select_one(".jp-Notebook")["data-jp-theme-light"] == "true"
    bootstrap = html.select_one("script[data-mkdocs-jupyter-mathjax]")
    assert json.loads(bootstrap["data-mkdocs-jupyter-mathjax"])["url"] == (
        "/chosen-mathjax.js"
    )
    assert "saved exporter output" in html.select_one(".jp-OutputArea").get_text()


def test_embedded_images_and_options_invalidate_cache_without_disabling_warm_hits(
    exporter_site,
):
    counter = exporter_site / "docs/execution-count.txt"
    write_notebook(
        exporter_site,
        markdown=f"# Cached notebook\n\n{MARKDOWN_IMAGE}",
        code=(
            "from pathlib import Path\n"
            "counter = Path('execution-count.txt')\n"
            "count = int(counter.read_text()) + 1 if counter.exists() else 1\n"
            "counter.write_text(str(count))\n"
            "print('execution number', count)"
        ),
    )
    options = {"embed_images": True}
    first = build_exporter_site(
        exporter_site, execute=True, html_exporter_options=options
    )
    embedded_image(first, "Meaningful Markdown image")
    assert counter.read_text() == "1"
    warm = build_exporter_site(
        exporter_site, execute=True, html_exporter_options=options
    )
    embedded_image(warm, "Meaningful Markdown image")
    assert counter.read_text() == "1"
    assert "execution number 1" in warm.select_one(".jp-OutputArea").get_text()

    image_path = exporter_site / "docs/assets/plot.png"
    revised_image = PNG + b"revised image content"
    image_path.write_bytes(revised_image)
    revised = build_exporter_site(
        exporter_site, execute=True, html_exporter_options=options
    )
    embedded_image(revised, "Meaningful Markdown image", revised_image)
    assert counter.read_text() == "2"

    image_path.unlink()
    removed = build_exporter_site(
        exporter_site, execute=True, html_exporter_options=options
    )
    assert removed.select_one('img[alt="Meaningful Markdown image"]')["src"] == (
        "assets/plot.png"
    )
    assert counter.read_text() == "3"

    image_path.write_bytes(PNG)
    restored = build_exporter_site(
        exporter_site, execute=True, html_exporter_options=options
    )
    embedded_image(restored, "Meaningful Markdown image")
    assert counter.read_text() == "4"

    changed_options = build_exporter_site(
        exporter_site,
        execute=True,
        html_exporter_options={
            "embed_images": True, "anchor_link_text": "Updated link"
        },
    )
    assert changed_options.select_one("h1 a.anchor-link").get_text() == "Updated link"
    assert counter.read_text() == "5"


def test_raw_html_image_changes_invalidate_embedded_output_cache(exporter_site):
    write_notebook(exporter_site, markdown=HTML_IMAGE)
    options = {"embed_images": True}
    first = build_exporter_site(exporter_site, html_exporter_options=options)
    embedded_image(first, "Meaningful HTML image")
    revised_image = PNG + b"new raw HTML image"
    (exporter_site / "docs/assets/plot.png").write_bytes(revised_image)
    revised = build_exporter_site(exporter_site, html_exporter_options=options)
    element = embedded_image(revised, "Meaningful HTML image", revised_image)
    assert element["width"] == "123"



def test_retargeted_image_symlink_invalidates_cached_embedded_bytes(exporter_site):
    first_image = exporter_site / "first.png"
    second_image = exporter_site / "second.png"
    first_image.write_bytes(PNG + b"first image")
    second_image.write_bytes(PNG + b"second image")
    image_link = exporter_site / "docs/assets/plot.png"
    image_link.unlink()
    image_link.symlink_to(first_image)
    write_notebook(exporter_site, markdown=MARKDOWN_IMAGE)
    options = {"embed_images": True}
    first = build_exporter_site(exporter_site, html_exporter_options=options)
    embedded_image(first, "Meaningful Markdown image", PNG + b"first image")

    image_link.unlink()
    image_link.symlink_to(second_image)
    retargeted = build_exporter_site(exporter_site, html_exporter_options=options)
    embedded_image(retargeted, "Meaningful Markdown image", PNG + b"second image")


def test_excluding_markdown_does_not_leave_notebook_toc_or_override_title(
    exporter_site,
):
    write_notebook(
        exporter_site, markdown="# Hidden notebook heading\n\n## Hidden section"
    )
    html = build_exporter_site(
        exporter_site, html_exporter_options={"exclude_markdown": True}
    )
    assert not html.select(".jupyter-wrapper h1, .jupyter-wrapper h2")
    has_hidden_toc = bool(
        html.select_one('.md-nav--secondary a[href="#hidden-section"]')
    )
    assert not has_hidden_toc
    assert "Hidden notebook heading" not in html.title.get_text()
    assert "saved exporter output" in html.select_one(".jp-OutputArea").get_text()


def test_excluding_anchor_links_preserves_heading_ids_and_notebook_toc(exporter_site):
    write_notebook(exporter_site, markdown="# Notebook heading\n\n## Real section")
    html = build_exporter_site(
        exporter_site, html_exporter_options={"exclude_anchor_links": True}
    )
    assert html.select_one(".jupyter-wrapper h1")["id"] == "notebook-heading"
    assert html.select_one(".jupyter-wrapper h2")["id"] == "real-section"
    permalinks = html.select(".jupyter-wrapper a.anchor-link")
    assert not permalinks
    assert html.select_one('.md-nav--secondary a[href="#real-section"]') is not None
