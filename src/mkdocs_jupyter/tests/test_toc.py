import os
import textwrap
from html import escape

import nbformat
import pytest
from bs4 import BeautifulSoup
from mkdocs.config import load_config
from mkdocs.structure.toc import AnchorLink, TableOfContents

from mkdocs_jupyter import plugin


@pytest.mark.parametrize(
    "test_file_path,expected_anchor_count",
    [  # make sure to update corresponding numbers if any file gets changed
        ("./mkdocs/docs/fail.ipynb", 0),
        ("./mkdocs/docs/backquote_toc_test.ipynb", 10),
        ("./mkdocs/docs/demo.ipynb", 16),
        ("./mkdocs/docs/ruby.ipynb", 11),
        ("./mkdocs/docs/variational-inference.ipynb", 23),
    ],
)
def test_anchors_count(test_file_path, expected_anchor_count) -> None:
    this_dir = os.path.dirname(os.path.realpath(__file__))
    test_file_dir = os.path.join(this_dir, test_file_path)

    config_file = os.path.join(this_dir, "mkdocs/base-with-nbs.yml")
    toc_depth = load_config(config_file)["plugins"]["mkdocs-jupyter"].config[
        "toc_depth"
    ]

    toc: TableOfContents = plugin.get_nb_toc(test_file_dir, toc_depth)[0]

    anchor_count = 0
    anchor_ids = []
    traverse_stack: list[AnchorLink] = list(toc)
    while traverse_stack:
        anchor = traverse_stack[0]

        # print("\t" * (anchor.level - 1) + f'{anchor.level} | {anchor.title}')
        anchor_count += 1
        anchor_ids.append(anchor.id)
        traverse_stack.remove(anchor)
        traverse_stack = anchor.children + traverse_stack

    if "backquote_toc_test" in test_file_path:
        html = plugin.convert.nb2html(test_file_dir)
        headings = BeautifulSoup(html, "html.parser").select(
            "h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]"
        )
        assert len(headings) == 10
        assert anchor_ids == [heading["id"] for heading in headings]
    assert anchor_count == expected_anchor_count


@pytest.mark.parametrize(
    "example",
    [
        pytest.param("```python\n# Not a title\n```", id="triple-backticks"),
        pytest.param(
            "````markdown\n```python\n# Not a title\n```\n# Still code\n````",
            id="four-backticks-containing-triple-backticks",
        ),
        pytest.param("~~~python\n# Not a title\n~~~", id="tildes"),
        pytest.param(
            "```PYTHON\n~~~\n# Not a title\n```",
            id="mixed-fence-markers-and-uppercase-language",
        ),
        pytest.param(
            "```python\n# Literal delimiter ```\n# Still a comment\n```",
            id="backticks-inside-code-do-not-close-fence",
        ),
    ],
)
@pytest.mark.parametrize("heading_before", [True, False])
@pytest.mark.parametrize("indent", range(4))
def test_fenced_code_is_excluded_from_toc_and_title(
    tmp_path, example, heading_before, indent
):
    """Comments in Markdown examples must not hide or replace real headings."""
    example = textwrap.indent(example, " " * indent)
    source = f"{example}\n\n# Real title\n\n## After example"
    expected = ["Real title", "After example"]
    if heading_before:
        source = f"# Before example\n\n{source}"
        expected.insert(0, "Before example")
    notebook_path = tmp_path / "fenced.ipynb"
    nbformat.write(
        nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell(source)]),
        notebook_path,
    )

    toc, title = plugin.get_nb_toc(str(notebook_path), 6)
    anchors = list(toc)
    assert title == expected[0]
    actual = []
    while anchors:
        anchor = anchors.pop(0)
        actual.append(anchor.title)
        anchors[0:0] = anchor.children
    assert actual == expected


@pytest.mark.parametrize("delimiter", ["`", "``", "```"])
def test_inline_code_heading_text_and_link_match_rendered_heading(tmp_path, delimiter):
    notebook_path = tmp_path / "inline-code.ipynb"
    nbformat.write(
        nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell(
                    f"# Using {delimiter}my_function(){delimiter} safely"
                )
            ]
        ),
        notebook_path,
    )

    toc, title = plugin.get_nb_toc(str(notebook_path), 6)
    html = plugin.convert.nb2html(str(notebook_path))
    heading = BeautifulSoup(html, "html.parser").h1

    assert title == "Using my_function() safely"
    assert list(toc)[0].title == "Using my_function() safely"
    assert list(toc)[0].url == "#using-my_function-safely"
    assert list(toc)[0].url == f"#{heading['id']}"


@pytest.mark.parametrize("delimiter", ["`", "``"])
def test_unmatched_inline_backticks_across_cells_preserve_headings(tmp_path, delimiter):
    notebook_path = tmp_path / "unmatched.ipynb"
    nbformat.write(
        nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell(f"Unmatched {delimiter}backticks"),
                nbformat.v4.new_markdown_cell("# First heading\n\n## Second heading"),
                nbformat.v4.new_markdown_cell(f"Another {delimiter}backtick"),
            ]
        ),
        notebook_path,
    )

    toc, title = plugin.get_nb_toc(str(notebook_path), 6)

    assert title == "First heading"
    assert list(toc)[0].title == "First heading"
    assert list(toc)[0].children[0].title == "Second heading"


@pytest.mark.parametrize("delimiter", ["```", "````", "~~~"])
def test_unclosed_fence_does_not_hide_headings_in_later_cells(tmp_path, delimiter):
    notebook_path = tmp_path / "unclosed-fence.ipynb"
    nbformat.write(
        nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell(
                    f"# First heading\n\n{delimiter}python\n# Still code"
                ),
                nbformat.v4.new_markdown_cell("## Later heading"),
            ]
        ),
        notebook_path,
    )

    toc, title = plugin.get_nb_toc(str(notebook_path), 6)
    html = plugin.convert.nb2html(str(notebook_path))
    headings = BeautifulSoup(html, "html.parser").select("h1[id], h2[id]")

    assert title == "First heading"
    assert [heading["id"] for heading in headings] == ["first-heading", "later-heading"]
    assert list(toc)[0].id == "first-heading"
    assert [anchor.id for anchor in list(toc)[0].children] == ["later-heading"]


@pytest.mark.parametrize(
    "source, expected_headings",
    [
        pytest.param(
            "- ```python\n  # Code\n  ```\n\n# After",
            [("after", "After")],
            id="fence-in-list",
        ),
        pytest.param(
            "<pre>\n```\n</pre>\n\n# After",
            [("after", "After")],
            id="literal-fence-in-raw-html",
        ),
        pytest.param(
            "Paragraph\n```python\n# Code\n```\n---",
            [],
            id="removed-fence-must-not-create-setext-heading",
        ),
        pytest.param(
            "> ```python\n> # Code\n> ```\n\n# After",
            [("after", "After")],
            id="fence-in-blockquote",
        ),
        pytest.param(
            "> # Quoted heading\n\n- ## List heading\n\nSetext heading\n===",
            [
                ("quoted-heading", "Quoted heading"),
                ("list-heading", "List heading"),
                ("setext-heading", "Setext heading"),
            ],
            id="headings-in-containers-and-setext",
        ),
    ],
)
def test_toc_matches_rendered_markdown_structure(tmp_path, source, expected_headings):
    notebook_path = tmp_path / "markdown-structure.ipynb"
    nbformat.write(
        nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell(source)]),
        notebook_path,
    )

    toc, title = plugin.get_nb_toc(str(notebook_path), 6)
    html = plugin.convert.nb2html(str(notebook_path))
    headings = BeautifulSoup(html, "html.parser").select(
        "h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]"
    )
    rendered = []
    for heading in headings:
        heading.select_one(".anchor-link").decompose()
        rendered.append((heading["id"], heading.get_text()))
    assert rendered == expected_headings
    anchors = list(toc)
    actual = []
    while anchors:
        anchor = anchors.pop(0)
        actual.append((anchor.id, anchor.title))
        anchors[0:0] = anchor.children
    assert actual == expected_headings
    assert title == (expected_headings[0][1] if expected_headings else None)


@pytest.mark.parametrize(
    "source, expected_title, expected_id",
    [
        ("# Using `[x](y)` safely", "Using [x](y) safely", "using-xy-safely"),
        ("# Using `![x](y)` safely", "Using ![x](y) safely", "using-xy-safely"),
        (r"# Using \*foo\* safely", "Using *foo* safely", "using-foo-safely"),
        ("# Using **foo** safely", "Using foo safely", "using-foo-safely"),
        ("# Using [x](y) safely", "Using x safely", "using-x-safely"),
        ("# Using `{#evil}` safely", "Using {#evil} safely", "using-evil-safely"),
        (
            "# Using `<tag> & [x](y)` safely",
            "Using <tag> & [x](y) safely",
            "using-tag-xy-safely",
        ),
        ("# Café **naïve**", "Café naïve", "cafe-naive"),
    ],
)
def test_toc_preserves_rendered_literal_text_and_actual_id(
    tmp_path, source, expected_title, expected_id
):
    notebook_path = tmp_path / "literal-heading.ipynb"
    nbformat.write(
        nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell(source)]),
        notebook_path,
    )

    toc, title = plugin.get_nb_toc(str(notebook_path), 6)
    html = plugin.convert.nb2html(str(notebook_path))
    heading = BeautifulSoup(html, "html.parser").h1
    heading.select_one(".anchor-link").decompose()

    assert heading.get_text() == expected_title
    assert heading["id"] == expected_id
    assert title == escape(expected_title, quote=False)
    assert list(toc)[0].title == escape(expected_title, quote=False)
    assert list(toc)[0].url == f"#{expected_id}"


def test_toc_preserves_repeated_actual_heading_ids(tmp_path):
    notebook_path = tmp_path / "repeated-headings.ipynb"
    nbformat.write(
        nbformat.v4.new_notebook(
            cells=[nbformat.v4.new_markdown_cell("# Same heading\n\n## Same heading")]
        ),
        notebook_path,
    )

    toc, _ = plugin.get_nb_toc(str(notebook_path), 6)
    html = plugin.convert.nb2html(str(notebook_path))
    headings = BeautifulSoup(html, "html.parser").select("h1[id], h2[id]")

    assert [heading["id"] for heading in headings] == ["same-heading", "same-heading"]
    assert list(toc)[0].id == "same-heading"
    assert list(toc)[0].children[0].id == "same-heading"


@pytest.mark.parametrize("underline, level", [("===", 1), ("---", 2)])
def test_multiline_setext_heading_preserves_all_text_and_actual_id(
    tmp_path, underline, level
):
    notebook_path = tmp_path / "multiline-setext.ipynb"
    nbformat.write(
        nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell(f"First line\nsecond line\n{underline}")
            ]
        ),
        notebook_path,
    )

    toc, title = plugin.get_nb_toc(str(notebook_path), 6)
    html = plugin.convert.nb2html(str(notebook_path))
    heading = BeautifulSoup(html, "html.parser").find(f"h{level}")
    heading.select_one(".anchor-link").decompose()

    assert heading.get_text() == "First line\nsecond line"
    assert heading["id"] == "first-line-second-line"
    assert list(toc)[0].title == "First line second line"
    assert list(toc)[0].url == "#first-line-second-line"
    assert title == ("First line second line" if level == 1 else None)
