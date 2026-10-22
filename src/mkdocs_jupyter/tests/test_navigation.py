import nbformat
import pytest
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config


@pytest.mark.parametrize("use_directory_urls", [True, False])
def test_notebooks_render_in_nested_navigation_on_cold_and_warm_builds(
    tmp_path, monkeypatch, use_directory_urls
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    docs = tmp_path / "docs"
    (docs / "api").mkdir(parents=True)
    (docs / "examples").mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs / "api/reference.md").write_text("# API reference\n", encoding="utf-8")
    for filename, title in [("main.ipynb", "Main"), ("examples/demo.ipynb", "Demo")]:
        nbformat.write(
            nbformat.v4.new_notebook(
                cells=[
                    nbformat.v4.new_markdown_cell(
                        f"# {title}\n\n{title} notebook content.\n\n## Details"
                    )
                ]
            ),
            docs / filename,
        )

    config_file = tmp_path / "mkdocs.yml"
    config_file.write_text(
        f"""site_name: Nested notebook navigation
strict: true
use_directory_urls: {str(use_directory_urls).lower()}
theme:
  name: material
plugins:
  - mkdocs-jupyter
nav:
  - Home: index.md
  - Source Code API Reference:
      - API reference: api/reference.md
  - Notebooks:
      - Main: main.ipynb
      - Examples:
          - Demo: examples/demo.ipynb
""",
        encoding="utf-8",
    )
    destinations = (
        {"Main": "main/index.html", "Demo": "examples/demo/index.html"}
        if use_directory_urls
        else {"Main": "main.html", "Demo": "examples/demo.html"}
    )
    expected_links = (
        {"Main": "main/", "Demo": "examples/demo/"}
        if use_directory_urls
        else {"Main": "main.html", "Demo": "examples/demo.html"}
    )

    for _ in range(2):
        build(load_config(str(config_file)))
        home = BeautifulSoup(
            (tmp_path / "site/index.html").read_text(encoding="utf-8"), "html.parser"
        )
        navigation = home.select_one(".md-nav--primary")
        sections = {
            item.find("label", class_="md-nav__link").get_text(" ", strip=True): item
            for item in navigation.select("li.md-nav__item--nested")
        }
        notebooks = sections["Notebooks"]
        assert {
            link.get_text(" ", strip=True): link["href"]
            for link in notebooks.select("a.md-nav__link")
        } == expected_links
        assert sections["Examples"] in notebooks.descendants
        assert (
            sections["Examples"].select_one("a.md-nav__link")["href"]
            == (expected_links["Demo"])
        )
        assert navigation.find(
            "a", href="api/reference/" if use_directory_urls else "api/reference.html"
        )

        for title, destination in destinations.items():
            page = BeautifulSoup(
                (tmp_path / "site" / destination).read_text(encoding="utf-8"),
                "html.parser",
            )
            notebook = page.select_one(".jupyter-wrapper")
            assert f"{title} notebook content." in notebook.get_text()
            assert notebook.select_one("h1")["id"] == title.lower()
            assert (
                page.select_one(".md-nav--primary a.md-nav__link--active").get_text(
                    " ", strip=True
                )
                == title
            )
