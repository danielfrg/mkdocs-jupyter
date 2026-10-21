import nbformat
import pytest
import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config


@pytest.fixture
def notebook_site(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    docs = tmp_path / "docs"
    (docs / "examples").mkdir(parents=True)
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                "print('fresh-output')",
                execution_count=1,
                outputs=[
                    nbformat.v4.new_output(
                        "stream", name="stdout", text="saved-output\n"
                    )
                ],
            )
        ],
        metadata={
            "kernelspec": {
                "name": "python3",
                "language": "python",
                "display_name": "Python 3",
            }
        },
    )
    for name in ("examples/selected", "examples/ignored", "other"):
        nbformat.write(notebook, docs / f"{name}.ipynb")
    return tmp_path


def build_notebook_site(root, options):
    config_file = root / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Notebook options",
                "plugins": [{"mkdocs-jupyter": options}],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(str(config_file)))
    return {
        name: BeautifulSoup(
            (root / "site" / name / "index.html").read_text(encoding="utf-8"),
            "html.parser",
        )
        for name in ("examples/selected", "examples/ignored", "other")
    }


def executed_pages(pages):
    return {
        name
        for name, page in pages.items()
        if "fresh-output"
        in "".join(output.get_text() for output in page.select(".jp-OutputArea-output"))
    }


@pytest.mark.parametrize(
    "options,expected",
    [
        ({}, set()),
        (
            {"execute": True},
            {"examples/selected", "examples/ignored", "other"},
        ),
        (
            {"execute": False, "execute_include": ["examples/*.ipynb"]},
            set(),
        ),
        (
            {
                "execute": True,
                "execute_include": ["examples/*.ipynb"],
                "execute_ignore": ["*/ignored.ipynb"],
            },
            {"examples/selected"},
        ),
        (
            {
                "execute": True,
                "execute_include": ["*/selected.ipynb", "other.ipynb"],
            },
            {"examples/selected", "other"},
        ),
        ({"execute": True, "execute_include": ["missing/*.ipynb"]}, set()),
        (
            {
                "execute": True,
                "execute_include": ["*/selected.ipynb"],
                "execute_ignore": ["*/selected.ipynb"],
            },
            set(),
        ),
    ],
)
def test_execution_filters(notebook_site, options, expected):
    pages = build_notebook_site(notebook_site, options)
    assert executed_pages(pages) == expected
    for page in pages.values():
        assert page.select(".jp-OutputArea-output")


def test_execution_include_changes_invalidate_cache(notebook_site):
    options = {"execute": True, "execute_include": ["*/selected.ipynb"]}
    first = build_notebook_site(notebook_site, options)
    assert executed_pages(first) == {"examples/selected"}

    options["execute_include"] = ["*/ignored.ipynb"]
    second = build_notebook_site(notebook_site, options)
    assert executed_pages(second) == {"examples/ignored"}


@pytest.mark.parametrize(
    "options,expected_src",
    [
        (
            {},
            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/latest.js?config=TeX-AMS_CHTML-full,Safe",
        ),
        (
            {"custom_mathjax_url": ""},
            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/latest.js?config=TeX-AMS_CHTML-full,Safe",
        ),
        (
            {"custom_mathjax_url": "/assets/mathjax.js?config=TeX-AMS_CHTML-full,Safe"},
            "/assets/mathjax.js?config=TeX-AMS_CHTML-full,Safe",
        ),
    ],
)
def test_mathjax_script_source(notebook_site, options, expected_src):
    pages = build_notebook_site(notebook_site, options)
    scripts = pages["examples/selected"].find_all("script", src=True)
    assert expected_src in [script["src"] for script in scripts]
    assert all(script["src"] for script in scripts)
