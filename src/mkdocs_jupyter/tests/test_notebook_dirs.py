from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import jupytext
import nbformat
import pytest
import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort, ConfigurationError, PluginError


KERNEL = {
    "name": "python3",
    "language": "python",
    "display_name": "Python 3",
}


def write_notebook(path, cells, fmt="ipynb"):
    path.parent.mkdir(parents=True, exist_ok=True)
    notebook = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": KERNEL})
    jupytext.write(notebook, path, fmt=fmt)
    return path.read_bytes()


def site_config(root, options=None, **settings):
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    config_file = root / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "External notebooks",
                "strict": True,
                "plugins": [
                    {
                        "mkdocs-jupyter": {
                            "notebook_dirs": {"examples": "notebooks"},
                            **(options or {}),
                        }
                    }
                ],
                **settings,
            }
        ),
        encoding="utf-8",
    )
    return config_file


def read_page(root, relative_path):
    return BeautifulSoup(
        (root / "site" / relative_path).read_text(encoding="utf-8"), "html.parser"
    )


def linked_site_file(root, page_url, reference):
    url = urlsplit(urljoin(f"https://docs.example/{page_url}", reference))
    assert url.netloc == "docs.example"
    path = root / "site" / unquote(url.path).lstrip("/")
    return path / "index.html" if url.path.endswith("/") else path


@pytest.mark.parametrize("processor", ["jupyter", "mkdocs"])
@pytest.mark.parametrize("use_directory_urls", [True, False])
def test_external_notebook_navigation_links_assets_and_watch(
    tmp_path, monkeypatch, use_directory_urls, processor
):
    # Missing source-backed registration, URL rewriting, or directory watching
    # must break a real build, a rendered link, or the registered watch path.
    source = tmp_path / "notebooks"
    write_notebook(
        source / "sub" / "demo.ipynb",
        [
            nbformat.v4.new_markdown_cell(
                "# External demo\n\n## Details\n\n"
                "![A useful figure](figure.svg)\n\n"
                "[Other notebook](../other.ipynb#other-details)"
            ),
            nbformat.v4.new_code_cell(
                "",
                outputs=[
                    nbformat.v4.new_output(
                        "display_data",
                        data={
                            "text/html": (
                                '<img alt="Rich output figure" '
                                'src="figure.svg">'
                            )
                        },
                    )
                ],
            ),
        ],
    )
    write_notebook(
        source / "other.ipynb",
        [nbformat.v4.new_markdown_cell("# Other\n\n## Other details")],
    )
    image = (
        b'<svg xmlns="http://www.w3.org/2000/svg"><title>Useful figure</title></svg>'
    )
    (source / "sub" / "figure.svg").write_bytes(image)
    # A second file with the same name catches accidentally rewriting a URL
    # that MkDocs has already made relative to the rendered page.
    (source / "figure.svg").write_bytes(b"<svg>Wrong parent figure</svg>")
    (source / ".private.txt").write_text("not public", encoding="utf-8")
    (source / ".hidden").mkdir()
    (source / ".hidden" / "secret.txt").write_text("not public", encoding="utf-8")
    config_file = site_config(
        tmp_path,
        {"markdown_cell_processor": processor},
        use_directory_urls=use_directory_urls,
        nav=[
            {"Home": "index.md"},
            {
                "Examples": [
                    {"External demo": "examples/sub/demo.ipynb"},
                    {"Other": "examples/other.ipynb"},
                ]
            },
        ],
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    cfg = load_config(str(config_file))
    build(cfg)

    destination = (
        "examples/sub/demo/index.html"
        if use_directory_urls
        else "examples/sub/demo.html"
    )
    page_url = "examples/sub/demo/" if use_directory_urls else "examples/sub/demo.html"
    page = read_page(tmp_path, destination)
    wrapper = page.select_one(".jupyter-wrapper")
    assert wrapper.select_one("h1")["id"] == "external-demo"
    assert wrapper.select_one("h2")["id"] == "details"
    assert page.find("a", href="#details")
    image_tag = wrapper.find("img", alt="A useful figure")
    assert linked_site_file(tmp_path, page_url, image_tag["src"]).read_bytes() == image
    rich_image = wrapper.find("img", alt="Rich output figure")
    assert linked_site_file(tmp_path, page_url, rich_image["src"]).read_bytes() == image
    notebook_link = wrapper.find("a", string="Other notebook")
    assert urlsplit(notebook_link["href"]).fragment == "other-details"
    other = linked_site_file(tmp_path, page_url, notebook_link["href"])
    assert other.is_file()
    other_heading = BeautifulSoup(
        other.read_text(encoding="utf-8"), "html.parser"
    ).select_one(".jupyter-wrapper h1")
    assert other_heading["id"] == "other"
    assert "Other" in other_heading.get_text()
    home = read_page(tmp_path, "index.html")
    nav_link = home.find("a", string="External demo")
    assert (
        linked_site_file(tmp_path, "", nav_link["href"])
        == tmp_path / "site" / destination
    )
    assert source.resolve() in {Path(path).resolve() for path in cfg.watch}
    assert not (tmp_path / "site/examples/.private.txt").exists()
    assert not (tmp_path / "site/examples/.hidden").exists()
    assert sorted(
        path.relative_to(tmp_path / "docs").as_posix()
        for path in (tmp_path / "docs").rglob("*")
        if path.is_file()
    ) == ["index.md"]


def test_external_execution_source_download_and_cache_rebuild(tmp_path, monkeypatch):
    # Execution must use the real notebook directory, never a copied docs tree.
    # A warm build must reuse conversion; changing the source must invalidate it.
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    source = tmp_path / "notebooks" / "nested"
    source.mkdir(parents=True)
    (source / "message.txt").write_text("sibling data", encoding="utf-8")
    notebook_path = source / "run.ipynb"
    original = write_notebook(
        notebook_path,
        [
            nbformat.v4.new_markdown_cell("# Source execution"),
            nbformat.v4.new_code_cell(
                "from pathlib import Path\n"
                "print(Path('message.txt').read_text())\n"
                "counter = Path('execution-count.txt')\n"
                "count = int(counter.read_text()) if counter.exists() else 0\n"
                "counter.write_text(str(count + 1))\n"
                "print('initial result')"
            ),
        ],
    )
    config_file = site_config(
        tmp_path,
        {
            "execute": True,
            "allow_errors": False,
            "include_source": True,
            "cache_dir": str(tmp_path / ".cache" / "notebooks"),
        },
        nav=[{"Home": "index.md"}, {"Run": "examples/nested/run.ipynb"}],
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    for _ in range(2):
        build(load_config(str(config_file)))
        page = read_page(tmp_path, "examples/nested/run/index.html")
        output = "".join(
            area.get_text() for area in page.select(".jp-OutputArea-output")
        )
        assert "sibling data" in output
        assert "initial result" in output
        assert (source / "execution-count.txt").read_text() == "1"
        assert (
            tmp_path / "site/examples/nested/run/run.ipynb"
        ).read_bytes() == original
        assert notebook_path.read_bytes() == original
        assert Path.cwd() == elsewhere

    notebook = nbformat.read(notebook_path, as_version=4)
    notebook.cells[-1].source = notebook.cells[-1].source.replace(
        "initial result", "changed result"
    )
    nbformat.write(notebook, notebook_path)
    updated = notebook_path.read_bytes()
    build(load_config(str(config_file)))
    page = read_page(tmp_path, "examples/nested/run/index.html")
    output = "".join(area.get_text() for area in page.select(".jp-OutputArea-output"))
    assert "changed result" in output
    assert "initial result" not in output
    assert (source / "execution-count.txt").read_text() == "2"
    assert (tmp_path / "site/examples/nested/run/run.ipynb").read_bytes() == updated
    assert notebook_path.read_bytes() == updated
    assert not list((tmp_path / "docs").rglob("*.ipynb"))


@pytest.mark.parametrize("fmt,suffix", [("py:percent", ".py"), ("md", ".md")])
def test_external_jupytext_notebooks(tmp_path, fmt, suffix):
    write_notebook(
        tmp_path / "notebooks" / f"demo{suffix}",
        [nbformat.v4.new_markdown_cell("# Jupytext notebook\n\nExternal content")],
        fmt=fmt,
    )
    config_file = site_config(
        tmp_path, nav=[{"Home": "index.md"}, {"Demo": f"examples/demo{suffix}"}]
    )
    build(load_config(str(config_file)))
    page = read_page(tmp_path, "examples/demo/index.html")
    assert "External content" in page.select_one(".jupyter-wrapper").get_text()


def test_external_notebooks_respect_include_and_ignore(tmp_path):
    sources = {}
    for name in ("selected", "ignored", "other"):
        sources[name] = write_notebook(
            tmp_path / "notebooks" / f"{name}.ipynb",
            [nbformat.v4.new_markdown_cell(f"# {name}")],
        )
    config_file = site_config(
        tmp_path,
        {
            "include": ["*selected.ipynb", "*ignored.ipynb"],
            "ignore": ["*ignored.ipynb"],
        },
    )
    build(load_config(str(config_file)))
    assert read_page(tmp_path, "examples/selected/index.html").select_one(
        ".jupyter-wrapper"
    )
    for name in ("ignored", "other"):
        assert (tmp_path / "site/examples" / f"{name}.ipynb").read_bytes() == sources[
            name
        ]
        assert not (tmp_path / "site/examples" / name / "index.html").exists()


@pytest.mark.parametrize("mount", ["../outside", "/absolute", "examples/../../outside"])
def test_external_mount_rejects_unsafe_documentation_paths(tmp_path, mount):
    (tmp_path / "notebooks").mkdir()
    config_file = site_config(tmp_path, {"notebook_dirs": {mount: "notebooks"}})
    with pytest.raises((ConfigurationError, PluginError), match="notebook_dirs|mount"):
        build(load_config(str(config_file)))


def test_external_mount_requires_existing_directory(tmp_path):
    config_file = site_config(tmp_path)
    with pytest.raises(
        (ConfigurationError, PluginError), match="notebooks|notebook_dirs"
    ):
        build(load_config(str(config_file)))


@pytest.mark.parametrize(
    "existing_path,contents",
    [
        ("examples/demo.ipynb", None),
        ("examples/demo.md", "# Existing page"),
        ("examples/figure.svg", "existing asset"),
    ],
)
def test_external_mount_reports_source_and_output_collisions(
    tmp_path, caplog, existing_path, contents
):
    write_notebook(
        tmp_path / "notebooks/demo.ipynb",
        [nbformat.v4.new_markdown_cell("# External page")],
    )
    (tmp_path / "notebooks/figure.svg").write_text("external asset", encoding="utf-8")
    destination = tmp_path / "docs" / existing_path
    destination.parent.mkdir(parents=True)
    if contents is None:
        write_notebook(destination, [nbformat.v4.new_markdown_cell("# Existing page")])
    else:
        destination.write_text(contents, encoding="utf-8")
    config_file = site_config(tmp_path)
    with pytest.raises(Abort):
        build(load_config(str(config_file)))
    assert "collision" in caplog.text
    assert existing_path in caplog.text


def test_external_mount_rejects_file_directory_output_collision(tmp_path, caplog):
    # A static file at the notebook's output directory must fail before MkDocs
    # tries to create an HTML child beneath that file.
    write_notebook(
        tmp_path / "notebooks/demo.ipynb",
        [nbformat.v4.new_markdown_cell("# Demo")],
    )
    existing = tmp_path / "docs/examples/demo"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"existing static file")
    config_file = site_config(tmp_path)
    with pytest.raises(Abort):
        build(load_config(str(config_file)))
    assert "output collision" in caplog.text
    assert "examples/demo" in caplog.text
    assert "examples/demo.ipynb" in caplog.text


@pytest.mark.parametrize("use_directory_urls", [True, False])
def test_external_url_rewriting_preserves_encoding_and_nonlocal_references(
    tmp_path, use_directory_urls
):
    # Resolving the asset must retain its query/fragment; external, embedded,
    # and same-page references must never be interpreted as local source files.
    embedded = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="
    remote = "https://images.example/a%20b.svg?version=2#remote"
    write_notebook(
        tmp_path / "notebooks/sub/demo.ipynb",
        [
            nbformat.v4.new_markdown_cell(
                "# Demo\n\n## Details\n\n"
                "![Encoded asset](figures/a%20b.svg?version=2#shape)\n\n"
                f"[Remote image]({remote})\n\n"
                "[Local anchor](#details)\n\n"
                f'<img alt="Embedded image" src="{embedded}">'
            )
        ],
    )
    asset = tmp_path / "notebooks/sub/figures/a b.svg"
    asset.parent.mkdir()
    contents = b'<svg xmlns="http://www.w3.org/2000/svg"><g id="shape"/></svg>'
    asset.write_bytes(contents)
    config_file = site_config(
        tmp_path,
        use_directory_urls=use_directory_urls,
        nav=[{"Home": "index.md"}, {"Demo": "examples/sub/demo.ipynb"}],
    )
    build(load_config(str(config_file)))
    destination = (
        "examples/sub/demo/index.html"
        if use_directory_urls
        else "examples/sub/demo.html"
    )
    page_url = "examples/sub/demo/" if use_directory_urls else "examples/sub/demo.html"
    wrapper = read_page(tmp_path, destination).select_one(".jupyter-wrapper")
    image = wrapper.find("img", alt="Encoded asset")
    reference = urlsplit(image["src"])
    assert reference.path.endswith("figures/a%20b.svg")
    assert reference.query == "version=2"
    assert reference.fragment == "shape"
    assert linked_site_file(tmp_path, page_url, image["src"]).read_bytes() == contents
    assert wrapper.find("a", string="Remote image")["href"] == remote
    assert wrapper.find("a", string="Local anchor")["href"] == "#details"
    assert wrapper.find("img", alt="Embedded image")["src"] == embedded


def test_external_source_inside_site_directory_is_rejected_before_cleaning(tmp_path):
    source = tmp_path / "site/notebooks/demo.ipynb"
    original = write_notebook(
        source, [nbformat.v4.new_markdown_cell("# Must be preserved")]
    )
    config_file = site_config(
        tmp_path, {"notebook_dirs": {"examples": "site/notebooks"}}
    )
    with pytest.raises(ConfigurationError, match="site_dir"):
        build(load_config(str(config_file)))
    assert source.read_bytes() == original


def test_mkdocs_exclude_docs_applies_to_mounted_files_and_collisions(tmp_path):
    # An excluded notebook must neither block an ordinary Markdown page with
    # the same output path nor be rendered/downloaded as a separate notebook.
    for name in ("demo", "hidden"):
        write_notebook(
            tmp_path / "notebooks" / f"{name}.ipynb",
            [nbformat.v4.new_markdown_cell(f"# Excluded {name}")],
        )
    (tmp_path / "notebooks/private.txt").write_text("private data", encoding="utf-8")
    docs = tmp_path / "docs/examples"
    docs.mkdir(parents=True)
    (docs / "demo.md").write_text("# Existing page\n", encoding="utf-8")
    config_file = site_config(
        tmp_path,
        {"include_source": True},
        exclude_docs="/examples/demo.ipynb\n/examples/hidden.ipynb\n/examples/private.txt\n",
        nav=[{"Home": "index.md"}, {"Existing page": "examples/demo.md"}],
    )
    build(load_config(str(config_file)))
    page = read_page(tmp_path, "examples/demo/index.html")
    assert "Existing page" in page.get_text()
    assert page.select_one(".jupyter-wrapper") is None
    assert not (tmp_path / "site/examples/hidden/index.html").exists()
    assert not list((tmp_path / "site").rglob("*.ipynb"))
    assert not (tmp_path / "site/examples/private.txt").exists()


def test_warm_cache_remaps_newly_added_mounted_asset(tmp_path):
    # URL mapping must run after reading cached notebook HTML: a new asset
    # should resolve without needing any notebook source edit.
    notebook_path = tmp_path / "notebooks/demo.ipynb"
    original = write_notebook(
        notebook_path,
        [nbformat.v4.new_markdown_cell("# Demo\n\n![New figure](figure.svg)")],
    )
    config_file = site_config(
        tmp_path,
        {"cache_dir": str(tmp_path / ".cache/notebooks")},
        nav=[{"Home": "index.md"}, {"Demo": "examples/demo.ipynb"}],
    )
    build(load_config(str(config_file)))
    first_image = read_page(tmp_path, "examples/demo/index.html").find(
        "img", alt="New figure"
    )
    assert not linked_site_file(tmp_path, "examples/demo/", first_image["src"]).exists()
    cache_files = list((tmp_path / ".cache/notebooks").glob("*.json"))
    assert len(cache_files) == 1
    cache_modified = cache_files[0].stat().st_mtime_ns
    contents = (
        b'<svg xmlns="http://www.w3.org/2000/svg"><title>Added later</title></svg>'
    )
    (tmp_path / "notebooks/figure.svg").write_bytes(contents)
    build(load_config(str(config_file)))
    second_image = read_page(tmp_path, "examples/demo/index.html").find(
        "img", alt="New figure"
    )
    assert (
        linked_site_file(tmp_path, "examples/demo/", second_image["src"]).read_bytes()
        == contents
    )
    assert cache_files[0].stat().st_mtime_ns == cache_modified
    assert notebook_path.read_bytes() == original
