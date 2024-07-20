import os

import pytest
from mkdocs.config import load_config
from mkdocs.structure.toc import AnchorLink, TableOfContents

from mkdocs_jupyter import plugin


@pytest.mark.parametrize(
    "test_file_path,expected_anchor_count",
    [  # make sure to update corresponding numbers if any file gets changed
        ("./mkdocs/docs/fail.ipynb", 0),
        ("./mkdocs/docs/backquote_toc_test.ipynb", 11),
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
    traverse_stack: list[AnchorLink] = list(toc)
    while traverse_stack:
        anchor = traverse_stack[0]

        # print("\t" * (anchor.level - 1) + f'{anchor.level} | {anchor.title}')
        anchor_count += 1
        traverse_stack.remove(anchor)
        traverse_stack = anchor.children + traverse_stack

    assert anchor_count == expected_anchor_count
