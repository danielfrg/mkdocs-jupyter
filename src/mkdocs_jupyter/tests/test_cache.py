import json
import os
import pathlib
import tempfile
from unittest.mock import patch

import pytest

from mkdocs_jupyter.plugin import _compute_cache_key, _get_cache_path


@pytest.fixture
def sample_nb(tmp_path):
    """Create a minimal .ipynb file for cache key tests."""
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Hello World"],
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_path = tmp_path / "test.ipynb"
    nb_path.write_text(json.dumps(nb))
    return nb_path


@pytest.fixture
def base_config():
    return {
        "execute": False,
        "kernel_name": "",
        "theme": "",
        "show_input": True,
        "no_input": False,
        "remove_tag_config": {},
        "highlight_extra_classes": "",
        "include_requirejs": False,
        "custom_mathjax_url": "",
        "toc_depth": 6,
    }


class TestComputeCacheKey:
    def test_same_file_same_config_same_key(self, sample_nb, base_config):
        key1 = _compute_cache_key(str(sample_nb), base_config)
        key2 = _compute_cache_key(str(sample_nb), base_config)
        assert key1 == key2

    def test_different_file_content_different_key(self, tmp_path, base_config):
        nb1 = tmp_path / "nb1.ipynb"
        nb2 = tmp_path / "nb2.ipynb"
        nb1.write_text(json.dumps({"cells": [], "metadata": {}, "nbformat": 4}))
        nb2.write_text(
            json.dumps(
                {"cells": [{"cell_type": "code"}], "metadata": {}, "nbformat": 4}
            )
        )

        key1 = _compute_cache_key(str(nb1), base_config)
        key2 = _compute_cache_key(str(nb2), base_config)
        assert key1 != key2

    def test_different_config_different_key(self, sample_nb, base_config):
        key1 = _compute_cache_key(str(sample_nb), base_config)

        config2 = {**base_config, "execute": True}
        key2 = _compute_cache_key(str(sample_nb), config2)
        assert key1 != key2

    def test_modified_file_different_key(self, sample_nb, base_config):
        key1 = _compute_cache_key(str(sample_nb), base_config)

        # Modify the file
        nb = json.loads(sample_nb.read_text())
        nb["cells"].append({"cell_type": "code", "metadata": {}, "source": ["x = 1"]})
        sample_nb.write_text(json.dumps(nb))

        key2 = _compute_cache_key(str(sample_nb), base_config)
        assert key1 != key2


class TestGetCachePath:
    def test_returns_json_path(self):
        path = _get_cache_path("/tmp/cache", "abc123")
        assert path == pathlib.Path("/tmp/cache/abc123.json")

    def test_path_under_cache_dir(self):
        path = _get_cache_path(".cache/mkdocs-jupyter", "deadbeef")
        assert str(path) == ".cache/mkdocs-jupyter/deadbeef.json"


class TestCacheIntegration:
    """Integration tests using full mkdocs build."""

    def test_cache_populated_on_first_build(self):
        """First build should create cache files."""
        from mkdocs.commands.build import build
        from mkdocs.config import load_config

        this_dir = os.path.dirname(os.path.realpath(__file__))
        config_file = os.path.join(this_dir, "mkdocs/base-with-nbs.yml")

        with tempfile.TemporaryDirectory() as cache_dir:
            cfg = load_config(config_file)
            cfg["plugins"]["mkdocs-jupyter"].config["cache"] = True
            cfg["plugins"]["mkdocs-jupyter"].config["cache_dir"] = cache_dir

            build(cfg)

            cache_files = list(pathlib.Path(cache_dir).glob("*.json"))
            assert len(cache_files) > 0, "Cache files should be created on first build"

    def test_cache_hit_on_second_build(self):
        """Second build should use cached results (nb2html not called again)."""
        from mkdocs.commands.build import build
        from mkdocs.config import load_config

        this_dir = os.path.dirname(os.path.realpath(__file__))
        config_file = os.path.join(this_dir, "mkdocs/base-with-nbs.yml")

        with tempfile.TemporaryDirectory() as cache_dir:
            cfg = load_config(config_file)
            cfg["plugins"]["mkdocs-jupyter"].config["cache"] = True
            cfg["plugins"]["mkdocs-jupyter"].config["cache_dir"] = cache_dir

            # First build populates cache
            build(cfg)

            # Second build should hit cache — nb2html should not be called
            cfg2 = load_config(config_file)
            cfg2["plugins"]["mkdocs-jupyter"].config["cache"] = True
            cfg2["plugins"]["mkdocs-jupyter"].config["cache_dir"] = cache_dir

            with patch("mkdocs_jupyter.convert.nb2html") as mock_nb2html:
                build(cfg2)
                mock_nb2html.assert_not_called()

    def test_cache_disabled(self):
        """When cache=False, no cache files should be created."""
        from mkdocs.commands.build import build
        from mkdocs.config import load_config

        this_dir = os.path.dirname(os.path.realpath(__file__))
        config_file = os.path.join(this_dir, "mkdocs/base-with-nbs.yml")

        with tempfile.TemporaryDirectory() as cache_dir:
            cfg = load_config(config_file)
            cfg["plugins"]["mkdocs-jupyter"].config["cache"] = False
            cfg["plugins"]["mkdocs-jupyter"].config["cache_dir"] = cache_dir

            build(cfg)

            cache_files = list(pathlib.Path(cache_dir).glob("*.json"))
            assert len(cache_files) == 0, "No cache files when cache is disabled"
