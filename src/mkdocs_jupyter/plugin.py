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
    )
    _supported_extensions = [".ipynb", ".py", ".md"]

    def should_include(self, file):
        ext = os.path.splitext(str(file.abs_src_path))[-1]
        if ext not in self._supported_extensions:
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
        srcpath = pathlib.PurePath(file.abs_src_path)
        include = None
        ignore = None
        for pattern in self.config["ignore"]:
            if srcpath.match(pattern):
                ignore = True
        for pattern in self.config["include"]:
            if srcpath.match(pattern):
                include = True
        return include and not ignore

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

            if self.config["execute_ignore"] and len(self.config["execute_ignore"]) > 0:
                for ignore_pattern in self.config["execute_ignore"]:
                    ignore_this = pathlib.PurePath(page.file.abs_src_path).match(
                        ignore_pattern
                    )
                    if ignore_this:
                        exec_nb = False

            theme = self.config["theme"]

            def new_render(self, config, files):
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
                )
                self.content = body
                toc, title = get_nb_toc(page.file.abs_src_path, toc_depth)
                self.toc = toc
                if title is not None and not ignore_h1_titles:
                    self.title = title

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
        if self.config["include_source"]:
            from shutil import copyfile

            nb_source = page.file.abs_src_path
            nb_source_name = os.path.basename(nb_source)
            nb_target_dir = os.path.dirname(page.file.abs_dest_path)
            nb_target = os.path.join(nb_target_dir, nb_source_name)

            os.makedirs(nb_target_dir, exist_ok=True)
            copyfile(nb_source, nb_target)
            print(f"Copied jupyter file: {nb_source} to {nb_target}")

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
            print(page.data_files)


def _get_markdown_toc(markdown_source, toc_depth):
    md = markdown.Markdown(extensions=[TocExtension(toc_depth=toc_depth)])
    md.convert(markdown_source)
    return md.toc_tokens


def get_nb_toc(fpath, toc_depth):
    """Returns a TOC for the Notebook
    It does that by converting first to MD
    """
    body = convert.nb2md(fpath)
    md_toc_tokens = _get_markdown_toc(body, toc_depth)
    toc = get_toc(md_toc_tokens)
    title = None
    for token in md_toc_tokens:
        if token["level"] == 1 and title is None:
            title = token["name"]
    return toc, title
