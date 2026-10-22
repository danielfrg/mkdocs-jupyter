from pathlib import Path

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
            "https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js",
        ),
        (
            {"custom_mathjax_url": ""},
            "https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js",
        ),
        (
            {"custom_mathjax_url": "/assets/mathjax/tex-mml-chtml.js"},
            "/assets/mathjax/tex-mml-chtml.js",
        ),
    ],
)
def test_mathjax_script_source(notebook_site, options, expected_src):
    pages = build_notebook_site(notebook_site, options)
    import json

    page = pages["examples/selected"]
    bootstrap = page.select_one("script[data-mkdocs-jupyter-mathjax]")
    assert json.loads(bootstrap["data-mkdocs-jupyter-mathjax"])["url"] == expected_src
    assert all(script["src"] for script in page.find_all("script", src=True))


@pytest.mark.parametrize(
    "fmt,suffix", [("ipynb", ".ipynb"), ("py:percent", ".py"), ("md", ".md")]
)
def test_execution_uses_source_directory_with_cold_and_warm_cache(
    tmp_path, monkeypatch, fmt, suffix
):
    import jupytext

    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    process_dir = tmp_path / "elsewhere"
    process_dir.mkdir()
    monkeypatch.chdir(process_dir)
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                "from pathlib import Path\n"
                "print(Path('message.txt').read_text())\n"
                "counter = Path('execution-count.txt')\n"
                "count = int(counter.read_text()) if counter.exists() else 0\n"
                "counter.write_text(str(count + 1))\n"
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
    originals = {}
    for name, message in (
        ("first", "first-directory-data"),
        ("second", "second-directory-data"),
    ):
        source_dir = tmp_path / "docs" / "examples" / name
        source_dir.mkdir(parents=True)
        (source_dir / "message.txt").write_text(message, encoding="utf-8")
        source = source_dir / f"notebook{suffix}"
        jupytext.write(notebook, source, fmt=fmt)
        originals[source] = source.read_bytes()
    config_file = tmp_path / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Source-relative execution",
                "plugins": [
                    {
                        "mkdocs-jupyter": {
                            "include": [f"*{suffix}"],
                            "execute": True,
                            "allow_errors": False,
                            "cache_dir": str(tmp_path / ".cache" / "notebooks"),
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    for _ in range(2):
        build(load_config(str(config_file)))
        for name, expected in (
            ("first", "first-directory-data"),
            ("second", "second-directory-data"),
        ):
            page = BeautifulSoup(
                (
                    tmp_path / "site" / "examples" / name / "notebook" / "index.html"
                ).read_text(encoding="utf-8"),
                "html.parser",
            )
            output = "".join(
                area.get_text() for area in page.select(".jp-OutputArea-output")
            )
            assert expected in output
            assert (
                tmp_path / "docs" / "examples" / name / "execution-count.txt"
            ).read_text() == "1"
        assert Path.cwd() == process_dir
        for source, original in originals.items():
            assert source.read_bytes() == original
