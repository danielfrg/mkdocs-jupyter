import hashlib
import json
import logging
import os
import pathlib
import re
from copy import copy

import jupytext
import markdown
import mkdocs
import yaml
from markdown.extensions.toc import TocExtension
from mkdocs.config import config_options
from mkdocs.exceptions import ConfigurationError, PluginError
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import get_toc

from . import convert
from .exporter_options import image_dependencies_valid, validate_html_exporter_options
from .markdown_cells import NotebookMarkdownExtension
from .metadata import get_notebook_metadata
from .mathjax import mathjax_script, mathjax_url
from .notebook_dirs import (
    check_collisions,
    configure_notebook_dirs,
    external_files,
    rewrite_notebook_urls,
)

logger = logging.getLogger("mkdocs.plugins.mkdocs_jupyter")


class NotebookFile(File):
    """
    Wraps a regular File object to make .ipynb files appear as
    valid documentation files.
    """

    def __init__(self, file, use_directory_urls, site_dir, **kwargs):
        self.file = file
        self.abs_src_path = file.abs_src_path
        if hasattr(file, "inclusion"):
            self.inclusion = file.inclusion
        if hasattr(file, "edit_uri"):
            self.edit_uri = file.edit_uri
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
        ("notebook_dirs", config_options.Type(dict, default={})),
        ("execute", config_options.Type(bool, default=False)),
        ("execute_include", config_options.Type(list, default=[])),
        ("execute_ignore", config_options.Type(list, default=[])),
        ("theme", config_options.Type(str, default="")),
        ("dark_scheme", config_options.Type(str, default="slate")),
        ("dark_selector", config_options.Type(str, default="")),
        ("kernel_name", config_options.Type(str, default="")),
        ("include_source", config_options.Type(bool, default=False)),
        ("ignore_h1_titles", config_options.Type(bool, default=False)),
        ("allow_errors", config_options.Type(bool, default=True)),
        ("show_input", config_options.Type(bool, default=True)),
        ("no_input", config_options.Type(bool, default=False)),
        ("no_prompt", config_options.Type(bool, default=False)),
        ("remove_tag_config", config_options.Type(dict, default={})),
        ("highlight_extra_classes", config_options.Type(str, default="")),
        ("include_requirejs", config_options.Type(bool, default=False)),
        ("toc_depth", config_options.Type(int, default=6)),
        ("data_files", config_options.Type(dict, default={})),
        (
            "markdown_cell_processor",
            config_options.Choice(("jupyter", "mkdocs"), default="jupyter"),
        ),
        ("html_exporter_options", config_options.Type(dict, default={})),
        ("custom_template", config_options.Optional(config_options.File(exists=True))),
        (
            "custom_mathjax_url",
            config_options.Type(str, default=""),
        ),
        ("mathjax_version", config_options.Choice((2, 3, 4), default=4)),
        ("cache", config_options.Type(bool, default=True)),
        ("cache_dir", config_options.Type(str, default=".cache/mkdocs-jupyter")),
    )
    _supported_extensions = [".ipynb", ".py", ".md"]

    def on_config(self, config):
        try:
            validate_html_exporter_options(self.config["html_exporter_options"])
        except ValueError as error:
            raise ConfigurationError(str(error)) from error
        self._notebook_dirs = configure_notebook_dirs(
            self.config["notebook_dirs"], config
        )
        dark_scheme = self.config["dark_scheme"]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", dark_scheme):
            raise ConfigurationError(
                "The mkdocs-jupyter dark_scheme option must be a CSS identifier."
            )

        dark_selector = self.config["dark_selector"]
        if dark_selector and (
            not dark_selector.strip() or re.search(r"[{};<\x00]", dark_selector)
        ):
            raise ConfigurationError(
                "The mkdocs-jupyter dark_selector option must be a CSS selector, "
                "without CSS rules or HTML."
            )

    def should_include(self, file):
        if file.abs_src_path is None:
            return False
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
        mounts = getattr(self, "_notebook_dirs", ())
        if mounts:
            known = {file.src_path for file in files}
            for file in external_files(mounts, config, self.config["cache_dir"]):
                if file.src_path in known:
                    raise PluginError(
                        "notebook_dirs source collision: "
                        f"{file.src_path!r} is already a documentation source."
                    )
                known.add(file.src_path)
                files.append(file)
        ret = Files(
            [
                NotebookFile(file, **config) if self.should_include(file) else file
                for file in files
            ]
        )
        if mounts:
            check_collisions(ret, self.config["include_source"])
        return ret

    def on_pre_page(self, page, config, files):
        if self.should_include(page.file):
            explicit_title = page.title
            ignore_h1_titles = self.config["ignore_h1_titles"]

            exec_nb = self.config["execute"]
            kernel_name = self.config["kernel_name"]
            allow_errors = self.config["allow_errors"]
            show_input = self.config["show_input"]
            no_input = self.config["no_input"]
            no_prompt = self.config["no_prompt"]
            remove_tag_config = self.config["remove_tag_config"]
            highlight_extra_classes = self.config["highlight_extra_classes"]
            include_requirejs = self.config["include_requirejs"]
            include_mermaidjs = config["theme"].name != "material"
            toc_depth = self.config["toc_depth"]
            custom_mathjax_url = self.config["custom_mathjax_url"]
            mathjax_version = self.config["mathjax_version"]
            processor = self.config["markdown_cell_processor"]

            if self.config["execute_include"]:
                exec_nb = exec_nb and any(
                    pathlib.PurePath(page.file.abs_src_path).match(pattern)
                    for pattern in self.config["execute_include"]
                )

            if self.config["execute_ignore"] and len(self.config["execute_ignore"]) > 0:
                for ignore_pattern in self.config["execute_ignore"]:
                    ignore_this = pathlib.PurePath(page.file.abs_src_path).match(
                        ignore_pattern
                    )
                    if ignore_this:
                        exec_nb = False

            theme = self.config["theme"]
            custom_template = self.config["custom_template"]
            html_exporter_options = self.config["html_exporter_options"]
            # Custom templates can depend on dynamic includes and local assets.
            cache_enabled = self.config["cache"] and not custom_template
            cache_dir = self.config["cache_dir"]

            if cache_enabled:
                cache_key = _compute_cache_key(
                    page.file.abs_src_path,
                    self.config,
                    exec_nb,
                    include_mermaidjs=include_mermaidjs,
                )
                cache_path = _get_cache_path(cache_dir, cache_key)
                self._used_cache_paths.add(cache_path)
            else:
                cache_path = None

            def notebook_content():
                if cache_path and cache_path.exists():
                    cached = json.loads(cache_path.read_text(encoding="utf-8"))
                    if image_dependencies_valid(cached.get("image_dependencies", {})):
                        logger.info("Cache hit: %s", page.file.abs_src_path)
                        return cached

                image_dependencies = {}
                body = convert.nb2html(
                    page.file.abs_src_path,
                    execute=exec_nb,
                    kernel_name=kernel_name,
                    theme=theme,
                    allow_errors=allow_errors,
                    show_input=show_input,
                    no_input=no_input,
                    no_prompt=no_prompt,
                    remove_tag_config=remove_tag_config,
                    highlight_extra_classes=highlight_extra_classes,
                    include_requirejs=include_requirejs,
                    include_mermaidjs=include_mermaidjs,
                    custom_mathjax_url=custom_mathjax_url,
                    custom_template=custom_template,
                    mathjax_version=mathjax_version,
                    include_mathjax=False,
                    markdown_cell_processor=processor,
                    html_exporter_options=html_exporter_options,
                    image_dependencies=image_dependencies,
                )
                # MkDocs mode derives headings from the configured Markdown pipeline.
                toc_tokens, title = (
                    _get_nb_toc_tokens(page.file.abs_src_path, toc_depth)
                    if processor == "jupyter"
                    and not html_exporter_options.get("exclude_markdown", False)
                    else ([], None)
                )
                converted = {
                    "content": body,
                    "toc_tokens": toc_tokens,
                    "title": title,
                    "image_dependencies": image_dependencies,
                }
                if cache_path:
                    logger.info("Cache miss, writing: %s", page.file.abs_src_path)
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_text(json.dumps(converted), encoding="utf-8")
                return converted

            def new_render(self, config, files):
                converted = notebook_content()
                self.content = converted["content"]
                self.toc = get_toc(converted["toc_tokens"])
                preserve_title = getattr(
                    self, "_mkdocs_jupyter_has_metadata", False
                ) and (explicit_title is not None or "title" in self.meta)
                if (
                    converted["title"] is not None
                    and not ignore_h1_titles
                    and not preserve_title
                ):
                    self.title = converted["title"]

            if processor == "mkdocs":
                page._mkdocs_jupyter_content = notebook_content
                original_render = page.render

                def mkdocs_render(self, config, files):
                    # Keep notebook-only extensions off ordinary Markdown pages.
                    page_config = copy(config)
                    extensions = list(config["markdown_extensions"])
                    if not any(
                        extension in ("md_in_html", "markdown.extensions.md_in_html")
                        for extension in extensions
                    ):
                        extensions.append("md_in_html")
                    set_title = (
                        not ignore_h1_titles
                        and explicit_title is None
                        and "title" not in self.meta
                    )
                    extensions.append(NotebookMarkdownExtension(self, set_title))
                    page_config["markdown_extensions"] = extensions
                    original_render(page_config, files)

                page.render = mkdocs_render.__get__(page, Page)
            else:
                # Replace render only for notebooks using nbconvert Markdown.
                page.render = new_render.__get__(page, Page)

            # Add metadata for template
            self._set_nb_url(page)
            page.data_files = self.config["data_files"].get(page.file.src_path)
        return page

    @mkdocs.plugins.event_priority(100)
    def on_page_markdown(self, markdown, page, config, files):
        if (
            self.config["markdown_cell_processor"] == "mkdocs"
            and self.should_include(page.file)
        ):
            if self.config["ignore_h1_titles"]:
                # Source reading supplied only metadata, so this is the nav,
                # metadata or filename title, before Markdown renders its H1.
                page.title = page.title
            return page._mkdocs_jupyter_content()["content"]
        return None

    def on_page_content(self, html, page, config, files):
        if (
            self.config["markdown_cell_processor"] == "mkdocs"
            and self.should_include(page.file)
        ):
            def limit_depth(items):
                retained = []
                for item in items:
                    if item.level <= self.config["toc_depth"]:
                        item.children = limit_depth(item.children)
                        retained.append(item)
                return retained

            page.toc.items = limit_depth(page.toc.items)
        if getattr(page.file, "_mkdocs_jupyter_mount", None) and self.should_include(
            page.file
        ):
            html = rewrite_notebook_urls(
                html,
                page.file,
                files,
                markdown_processed=self.config["markdown_cell_processor"] == "mkdocs",
            )
        return html

    def on_page_read_source(self, page, config):
        if not self.should_include(page.file):
            return None
        metadata = get_notebook_metadata(
            jupytext.read(page.file.abs_src_path), page.file.src_path
        )
        page._mkdocs_jupyter_has_metadata = metadata is not None
        if metadata is not None:
            # Let MkDocs populate page.meta during its normal source-read phase.
            # Leave notebook headings to our renderer so ignore_h1_titles also
            # works with MkDocs versions that determine titles during reading.
            return "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n"
        if self.config["markdown_cell_processor"] == "mkdocs":
            # Raw notebook JSON/Python is not page Markdown. The page_markdown
            # event supplies the converted notebook after MkDocs reads metadata.
            return ""
        return None

    def _set_nb_url(self, page):
        from urllib.parse import urljoin

        nb_source = page.file.abs_src_path
        nb_source_name = os.path.basename(nb_source)
        page.nb_url = urljoin(page.abs_url, nb_source_name)

    def on_post_page(self, output_content, page, config):
        if self.config["mathjax_version"] != 2:
            # Install before the first notebook is reached with instant navigation.
            script = mathjax_script(
                self.config["mathjax_version"], self.config["custom_mathjax_url"]
            )
            output_content = output_content.replace("</body>", script + "\n</body>")
        dark_scheme = self.config["dark_scheme"]
        dark_selector = self.config["dark_selector"]
        if dark_selector or dark_scheme != "slate":
            # :is() keeps every branch of a selector list scoped to each
            # descendant rule, e.g. :is(.dark, [data-theme="dark"]) .jupyter-wrapper.
            selector = (
                f":is({dark_selector})"
                if dark_selector
                else f'[data-md-color-scheme="{dark_scheme}"]'
            )
            output_content = output_content.replace(
                "[data-md-color-scheme=slate]", selector
            )

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

        return output_content

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
    md = markdown.Markdown(extensions=["attr_list", TocExtension(toc_depth=toc_depth)])
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


def _compute_cache_key(nb_path, config, exec_nb, include_mermaidjs=True):
    """Compute a SHA-256 hash from notebook content and relevant config options.

    Uses the resolved exec_nb value (after execution filters) rather
    than config["execute"], so that notebooks in execute_ignore get a distinct
    cache key.
    """
    hasher = hashlib.sha256()
    # Bump the cache format when rendering or TOC semantics change.
    hasher.update(b"mkdocs-jupyter-cache-v5\0")
    # Identical sources can read different data relative to their directories.
    hasher.update(os.fsencode(os.path.abspath(nb_path)))
    hasher.update(b"\0")
    hasher.update(pathlib.Path(nb_path).read_bytes())
    hasher.update(f"execute={exec_nb}".encode())
    hasher.update(f"include_mermaidjs={include_mermaidjs}".encode())
    hasher.update(f"mathjax_version={config.get('mathjax_version', 4)}".encode())
    processor = config.get("markdown_cell_processor", "jupyter")
    hasher.update(f"markdown_cell_processor={processor}".encode())
    hasher.update(repr(config.get("html_exporter_options", {})).encode())
    for key in (
        "kernel_name",
        "theme",
        "allow_errors",
        "show_input",
        "no_input",
        "no_prompt",
        "remove_tag_config",
        "highlight_extra_classes",
        "include_requirejs",
        "custom_mathjax_url",
        "toc_depth",
    ):
        value = config[key]
        if key == "custom_mathjax_url":
            value = mathjax_url(config.get("mathjax_version", 4), value)
        hasher.update(f"{key}={repr(value)}".encode())
    return hasher.hexdigest()


def _get_cache_path(cache_dir, cache_key):
    """Return the Path for a given cache key."""
    return pathlib.Path(cache_dir) / f"{cache_key}.json"
