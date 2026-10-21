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


@pytest.mark.parametrize(
    "selector",
    [
        ".dark",
        '[data-theme="dark"]',
        '[data-bs-theme="dark"]',
        "html.dark > body",
        '.dark, [data-theme="dark"]',
    ],
)
def test_custom_dark_selector_overrides_material_scheme(selector):
    plugin = Plugin()
    errors, _ = plugin.load_config({"dark_scheme": "night", "dark_selector": selector})
    assert not errors
    plugin.on_config(config={})
    page = SimpleNamespace(file=SimpleNamespace(src_path="example.ipynb"))
    output = (
        "<style>[data-md-color-scheme=slate] .jupyter-wrapper { color: white; }"
        "[data-md-color-scheme=slate] .highlight { color: white; }</style>"
        "<p>slate</p>"
    )

    result = plugin.on_post_page(output, page, config={})

    assert f":is({selector}) .jupyter-wrapper {{ color: white; }}" in result
    assert f":is({selector}) .highlight {{ color: white; }}" in result
    assert "data-md-color-scheme" not in result
    assert "<p>slate</p>" in result


@pytest.mark.parametrize(
    "selector", ["   ", ".dark { color: red; }", ".dark;", "</style><script>"]
)
def test_rejects_dark_selector_with_css_rules_or_html(selector):
    plugin = Plugin()
    plugin.load_config({"dark_selector": selector})

    with pytest.raises(ConfigurationError, match="dark_selector"):
        plugin.on_config(config={})


def test_custom_dark_selector_applies_to_cached_notebooks(tmp_path, monkeypatch):
    import nbformat
    import yaml
    from mkdocs.commands.build import build
    from mkdocs.config import load_config

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    docs = tmp_path / "docs"
    docs.mkdir()
    nbformat.write(
        nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("2 + 3")]),
        docs / "example.ipynb",
    )
    config_file = tmp_path / "mkdocs.yml"
    for selector in [".dark", '[data-theme="dark"]']:
        config_file.write_text(
            yaml.safe_dump(
                {
                    "site_name": "Dark selectors",
                    "plugins": [{"mkdocs-jupyter": {"dark_selector": selector}}],
                }
            ),
            encoding="utf-8",
        )
        build(load_config(str(config_file)))
        html = (tmp_path / "site/example/index.html").read_text(encoding="utf-8")
        assert f":is({selector}) .jupyter-wrapper" in html
        assert "[data-md-color-scheme=slate]" not in html
    assert len(list((tmp_path / ".cache/mkdocs-jupyter").glob("*.json"))) == 1
