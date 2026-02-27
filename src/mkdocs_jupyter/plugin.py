import hashlib
import json
import logging
import os
import pathlib

import jupytext
import markdown
import mkdocs
from markdown.extensions.toc import TocExtension
from mkdocs.config import config_options
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import get_toc

from . import convert

logger = logging.getLogger("mkdocs.plugins.mkdocs_jupyter")


class NotebookFile(File):
    """
    Wraps a regular File object to make .ipynb files appear as
    valid documentation files.
    """

    def __init__(self, file, use_directory_urls, site_dir, **kwargs):
        self.file = file
        self.dest_path = self._get_dest_path(use_directory_urls)
        self.abs_dest_path = os.path.normpath(os.path.join(site_dir, self.dest_path))
        self.url = self._get_url(use_directory_urls)

    def __getattr__(self, item):
        return self.file.__getattribute__(item)

    def is_documentation_page(self):
        return True


class Plugin(mkdocs.plugins.BasePlugin):
    config_scheme = (
        ("include", config_options.Type(list, default=["*.py", "*.ipynb", "*.md"])),
        ("ignore", config_options.Type(list, default=[])),
        ("execute", config_options.Type(bool, default=False)),
        ("execute_ignore", config_options.Type(list, default=[])),
        ("theme", config_options.Type(str, default="")),
        ("kernel_name", config_options.Type(str, default="")),
        ("include_source", config_options.Type(bool, default=False)),
        ("ignore_h1_titles", config_options.Type(bool, default=False)),
        ("allow_errors", config_options.Type(bool, default=True)),
        ("show_input", config_options.Type(bool, default=True)),
        ("no_input", config_options.Type(bool, default=False)),
        ("remove_tag_config", config_options.Type(dict, default={})),
        ("highlight_extra_classes", config_options.Type(str, default="")),
        ("include_requirejs", config_options.Type(bool, default=False)),
        ("toc_depth", config_options.Type(int, default=6)),
        ("data_files", config_options.Type(dict, default={})),
        ("custom_mathjax_url", config_options.Type(str, default="")),
        ("cache", config_options.Type(bool, default=True)),
        ("cache_dir", config_options.Type(str, default=".cache/mkdocs-jupyter")),
    )
    _supported_extensions = [".ipynb", ".py", ".md"]

    def should_include(self, file):
        srcpath = pathlib.PurePath(file.abs_src_path)
        ext = os.path.splitext(str(file.abs_src_path))[-1]
        if ext not in self._supported_extensions:
            return False
        for pattern in self.config["ignore"]:
            # check ignore patterns before attempting to read the file
            if srcpath.match(pattern):
                return False
        if ext == ".md":
            # only include markdown files with jupytext frontmatter
            # that explicitly specifies a python kernel
            try:
                data = jupytext.read(file.abs_src_path)
                if not (
                    (meta := data.get("metadata", {}))
                    and (kernelspec := meta.get("kernelspec"))
                    and kernelspec["language"] == "python"
                ):
                    return False
            except Exception:
                return False
        for pattern in self.config["include"]:
            if srcpath.match(pattern):
                return True
        return False

    def on_pre_build(self, config):
        self._used_cache_paths = set()

    def on_files(self, files, config):
        ret = Files(
            [
                NotebookFile(file, **config) if self.should_include(file) else file
                for file in files
            ]
        )
        return ret

    def on_pre_page(self, page, config, files):
        if self.should_include(page.file):
            ignore_h1_titles = self.config["ignore_h1_titles"]

            exec_nb = self.config["execute"]
            kernel_name = self.config["kernel_name"]
            allow_errors = self.config["allow_errors"]
            show_input = self.config["show_input"]
            no_input = self.config["no_input"]
            remove_tag_config = self.config["remove_tag_config"]
            highlight_extra_classes = self.config["highlight_extra_classes"]
            include_requirejs = self.config["include_requirejs"]
            toc_depth = self.config["toc_depth"]
            custom_mathjax_url = self.config["custom_mathjax_url"]

            if self.config["execute_ignore"] and len(self.config["execute_ignore"]) > 0:
                for ignore_pattern in self.config["execute_ignore"]:
                    ignore_this = pathlib.PurePath(page.file.abs_src_path).match(
                        ignore_pattern
                    )
                    if ignore_this:
                        exec_nb = False

            theme = self.config["theme"]
            cache_enabled = self.config["cache"]
            cache_dir = self.config["cache_dir"]

            if cache_enabled:
                cache_key = _compute_cache_key(
                    page.file.abs_src_path, self.config, exec_nb
                )
                cache_path = _get_cache_path(cache_dir, cache_key)
                self._used_cache_paths.add(cache_path)
            else:
                cache_path = None

            def new_render(self, config, files):
                if cache_path and cache_path.exists():
                    logger.info("Cache hit: %s", page.file.abs_src_path)
                    cached = json.loads(cache_path.read_text(encoding="utf-8"))
                    self.content = cached["content"]
                    self.toc = get_toc(cached["toc_tokens"])
                    if cached.get("title") is not None and not ignore_h1_titles:
                        self.title = cached["title"]
                    return

                body = convert.nb2html(
                    page.file.abs_src_path,
                    execute=exec_nb,
                    kernel_name=kernel_name,
                    theme=theme,
                    allow_errors=allow_errors,
                    show_input=show_input,
                    no_input=no_input,
                    remove_tag_config=remove_tag_config,
                    highlight_extra_classes=highlight_extra_classes,
                    include_requirejs=include_requirejs,
                    custom_mathjax_url=custom_mathjax_url,
                )
                self.content = body
                toc_tokens, title = _get_nb_toc_tokens(
                    page.file.abs_src_path, toc_depth
                )
                self.toc = get_toc(toc_tokens)
                if title is not None and not ignore_h1_titles:
                    self.title = title

                if cache_path:
                    logger.info("Cache miss, writing: %s", page.file.abs_src_path)
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_text(
                        json.dumps(
                            {
                                "content": body,
                                "toc_tokens": toc_tokens,
                                "title": title,
                            }
                        ),
                        encoding="utf-8",
                    )

            # replace render with new_render for this object only
            page.render = new_render.__get__(page, Page)

            # Add metadata for template
            self._set_nb_url(page)
            page.data_files = self.config["data_files"].get(page.file.src_path)
        return page

    def _set_nb_url(self, page):
        from urllib.parse import urljoin

        nb_source = page.file.abs_src_path
        nb_source_name = os.path.basename(nb_source)
        page.nb_url = urljoin(page.abs_url, nb_source_name)

    def on_post_page(self, output_content, page, config):
        # Include source
        if self.config["include_source"] and self.should_include(page.file):
            from shutil import copyfile

            nb_source = page.file.abs_src_path
            nb_source_name = os.path.basename(nb_source)
            nb_target_dir = os.path.dirname(page.file.abs_dest_path)
            nb_target = os.path.join(nb_target_dir, nb_source_name)

            os.makedirs(nb_target_dir, exist_ok=True)
            copyfile(nb_source, nb_target)
            logger.info("Copied jupyter file: %s to %s", nb_source, nb_target)

        # Include data files
        data_files = self.config["data_files"].get(page.file.src_path, [])
        if data_files:
            for data_file in data_files:
                data_source = data_file
                data_source_name = os.path.basename(data_file)
                data_target_dir = os.path.dirname(
                    os.path.join(nb_target_dir, data_source)
                )
                data_target = os.path.join(data_target_dir, data_source_name)

                os.makedirs(data_target_dir, exist_ok=True)
                copyfile(data_source, data_target)
            logger.info("Copied data files: %s to %s", data_files, data_target_dir)

    def on_post_build(self, config):
        if not self.config["cache"]:
            return
        cache_dir = pathlib.Path(self.config["cache_dir"])
        if not cache_dir.is_dir():
            return
        for cache_file in cache_dir.glob("*.json"):
            if cache_file not in self._used_cache_paths:
                cache_file.unlink()
                logger.info("Evicted stale cache: %s", cache_file)


def _get_markdown_toc(markdown_source, toc_depth):
    md = markdown.Markdown(extensions=[TocExtension(toc_depth=toc_depth)])
    md.convert(markdown_source)
    return md.toc_tokens


def _get_nb_toc_tokens(fpath, toc_depth):
    """Returns raw TOC tokens and title for the Notebook.

    Converts to Markdown first, then extracts TOC tokens.
    Returns (toc_tokens, title) where toc_tokens is a list of dicts.
    """
    body = convert.nb2md(fpath)
    md_toc_tokens = _get_markdown_toc(body, toc_depth)
    title = None
    for token in md_toc_tokens:
        if token["level"] == 1 and title is None:
            title = token["name"]
    return md_toc_tokens, title


def get_nb_toc(fpath, toc_depth):
    """Returns a TOC for the Notebook
    It does that by converting first to MD
    """
    md_toc_tokens, title = _get_nb_toc_tokens(fpath, toc_depth)
    toc = get_toc(md_toc_tokens)
    return toc, title


def _compute_cache_key(nb_path, config, exec_nb):
    """Compute a SHA-256 hash from notebook content and relevant config options.

    Uses the resolved exec_nb value (after execute_ignore processing) rather
    than config["execute"], so that notebooks in execute_ignore get a distinct
    cache key.
    """
    hasher = hashlib.sha256()
    hasher.update(pathlib.Path(nb_path).read_bytes())
    hasher.update(f"execute={exec_nb}".encode())
    for key in (
        "kernel_name",
        "theme",
        "allow_errors",
        "show_input",
        "no_input",
        "remove_tag_config",
        "highlight_extra_classes",
        "include_requirejs",
        "custom_mathjax_url",
        "toc_depth",
    ):
        hasher.update(f"{key}={repr(config[key])}".encode())
    return hasher.hexdigest()


def _get_cache_path(cache_dir, cache_key):
    """Return the Path for a given cache key."""
    return pathlib.Path(cache_dir) / f"{cache_key}.json"
