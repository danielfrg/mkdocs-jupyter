from types import SimpleNamespace

import pytest
from mkdocs.exceptions import ConfigurationError

from mkdocs_jupyter.plugin import Plugin


def test_on_post_page_uses_configured_dark_scheme():
    page = SimpleNamespace(file=SimpleNamespace(src_path="docs/example.ipynb"))
    output = (
        "<style>[data-md-color-scheme=slate] .jupyter-wrapper { color: white; }"
        "[data-md-color-scheme=slate] .highlight { color: white; }"
        "/* translate(slate) remains text */"
        "</style>"
    )

    default_plugin = Plugin()
    default_plugin.load_config({})
    assert default_plugin.on_post_page(output, page, config=None) == output

    plugin = Plugin()
    plugin.load_config({"dark_scheme": "dark"})
    result = plugin.on_post_page(output, page, config=None)

    assert result.count('[data-md-color-scheme="dark"]') == 2
    assert "translate(slate)" in result


def test_on_config_rejects_invalid_dark_scheme_selector():
    plugin = Plugin()
    plugin.load_config({"dark_scheme": 'dark"] { body { color: red'})

    with pytest.raises(ConfigurationError, match="dark_scheme"):
        plugin.on_config(config={})
