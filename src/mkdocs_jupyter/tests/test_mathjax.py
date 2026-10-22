import json

import nbformat
import pytest
import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config

from mkdocs_jupyter import convert
from mkdocs_jupyter.plugin import Plugin


DEFAULTS = {
    2: "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/latest.js?config=TeX-AMS_CHTML-full,Safe",
    3: "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js",
    4: "https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js",
}


def write_math_notebook(path):
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell(
                "# Math\n\nInline $x^2$ and code `$never$`.\n\n"
                "$$\\frac{1}{2}$$\n\n"
                r"\begin{equation}\label{eq:one}E=mc^2\end{equation}"
                "\n\n" + r"Reference $\eqref{eq:one}$."
            ),
            nbformat.v4.new_code_cell(
                "# Saved formula",
                outputs=[
                    nbformat.v4.new_output(
                        "display_data", data={"text/latex": r"$\displaystyle x+1$"}
                    )
                ],
            ),
        ]
    )
    nbformat.write(notebook, path)


@pytest.mark.parametrize("version", [2, 3, 4])
@pytest.mark.parametrize("custom", ["", "/assets/self-hosted.js?local=yes"])
def test_mathjax_version_and_custom_url(tmp_path, version, custom):
    notebook = tmp_path / "math.ipynb"
    write_math_notebook(notebook)
    html = BeautifulSoup(
        convert.nb2html(
            str(notebook), mathjax_version=version, custom_mathjax_url=custom
        ),
        "html.parser",
    )
    if version == 2:
        assert html.find("script", src=custom or DEFAULTS[version])
        assert "MathJax.Hub.Config" in str(html)
    else:
        bootstrap = html.select_one("script[data-mkdocs-jupyter-mathjax]")
        assert bootstrap is not None
        assert json.loads(bootstrap["data-mkdocs-jupyter-mathjax"]) == {
            "url": custom or DEFAULTS[version],
            "version": version,
        }
        assert html.select_one(".arithmatex").get_text() == r"\(x^2\)"
        assert html.select_one(
            '[data-mime-type="text/latex"] .arithmatex'
        ).get_text() == (r"\(\displaystyle x+1\)")
        assert "MathJax.Hub.Config" not in str(html)
    assert html.select_one("code").get_text() == "$never$"


def test_mathjax_default_is_four(tmp_path):
    notebook = tmp_path / "math.ipynb"
    write_math_notebook(notebook)
    html = BeautifulSoup(convert.nb2html(str(notebook)), "html.parser")
    bootstrap = html.select_one("script[data-mkdocs-jupyter-mathjax]")
    assert json.loads(bootstrap["data-mkdocs-jupyter-mathjax"])["url"] == DEFAULTS[4]


@pytest.mark.parametrize("version", [2, 3, 4])
def test_mathjax_runtime_is_available_before_first_instant_notebook(
    tmp_path, monkeypatch, version
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n\n[Notebook](math.ipynb)")
    write_math_notebook(docs / "math.ipynb")
    config = tmp_path / "mkdocs.yml"
    config.write_text(
        yaml.safe_dump(
            {
                "site_name": "Math",
                "theme": {"name": "material", "features": ["navigation.instant"]},
                "plugins": [{"mkdocs-jupyter": {"mathjax_version": version}}],
            }
        )
    )
    for _ in range(2):
        build(load_config(str(config)))
        home = BeautifulSoup((tmp_path / "site/index.html").read_text(), "html.parser")
        notebook = BeautifulSoup(
            (tmp_path / "site/math/index.html").read_text(), "html.parser"
        )
        for page in [home, notebook]:
            assert len(page.select("script[data-mkdocs-jupyter-mathjax]")) == (
                0 if version == 2 else 1
            )
        if version == 2:
            assert notebook.find("script", src=DEFAULTS[2])
        else:
            assert not notebook.find("script", src=DEFAULTS[version])


@pytest.mark.parametrize("version", [0, 5, "3"])
def test_invalid_mathjax_version_is_rejected(version):
    plugin = Plugin()
    errors, _ = plugin.load_config({"mathjax_version": version})
    assert any(name == "mathjax_version" for name, _ in errors)


@pytest.mark.parametrize("version", [2, 3, 4])
def test_mathjax_math_headings_keep_matching_toc_and_attachments(tmp_path, version):
    from mkdocs_jupyter.plugin import get_nb_toc

    notebook = tmp_path / "math.ipynb"
    cell = nbformat.v4.new_markdown_cell(
        "# Math $x_1$\n\n## Fraction $\\frac{a}{b}$\n\n"
        "![A tiny picture](attachment:tiny.png)"
    )
    cell.attachments = {"tiny.png": {"image/png": "aW1hZ2U="}}
    nbformat.write(nbformat.v4.new_notebook(cells=[cell]), notebook)
    html = BeautifulSoup(
        convert.nb2html(str(notebook), mathjax_version=version), "html.parser"
    )
    toc, _ = get_nb_toc(str(notebook), 6)
    assert [item.url for item in toc] == ["#" + html.h1["id"]]
    assert toc.items[0].children[0].url == "#" + html.h2["id"]
    assert html.select_one("img")["src"] == "data:image/png;base64,aW1hZ2U="
    assert html.select_one("img")["alt"] == "A tiny picture"


@pytest.mark.parametrize(
    "source,expected",
    [
        (r"$x$", r"\(x\)"),
        (r"$$x$$", r"\[x\]"),
        (r"$x$ and $y$", r"\(x\) and \(y\)"),
        ("$$x$$\n$$y$$", "\\[x\\]\n\\[y\\]"),
        (r"Before $x$ after $$y$$.", r"Before \(x\) after \[y\]."),
        (r"A price of \$5 and $x$", r"A price of \$5 and \(x\)"),
        (r"$\text{price \$5}$", r"\(\text{price \$5}\)"),
        (r"\(x\) and \[y\]", r"\(x\) and \[y\]"),
        (r"\(\text{$x$}\)", r"\(\text{$x$}\)"),
        (r"\begin{equation}x\end{equation}", r"\begin{equation}x\end{equation}"),
        (
            r"\begin{equation}\text{$x$}\end{equation}",
            r"\begin{equation}\text{$x$}\end{equation}",
        ),
        (r"Unpaired $ and bare x_1", r"Unpaired $ and bare x_1"),
    ],
)
def test_latex_output_preserves_math_regions(source, expected):
    from mkdocs_jupyter.mathjax import normalize_latex_output

    assert normalize_latex_output(source) == expected
