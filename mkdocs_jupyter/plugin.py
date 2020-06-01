import os

import mkdocs
from mkdocs.config import config_options
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import get_toc
from mkdocs.tests.base import get_markdown_toc

from . import convert


class NotebookFile(mkdocs.structure.files.File):
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
        ("execute", config_options.Type(bool, default=False)),
        ("include_source", config_options.Type(bool, default=False)),
    )

    def on_files(self, files, config):
        ret = Files(
            [
                NotebookFile(file, **config)
                if str(file.abs_src_path).endswith("ipynb")
                else file
                for file in files
            ]
        )
        return ret

    def on_pre_page(self, page, config, files):
        if str(page.file.abs_src_path).endswith(".ipynb"):
            exec_nb = self.config["execute"]

            def new_render(self, config, files):
                body = convert.nb2html(page.file.abs_src_path, execute=exec_nb)
                self.content = body
                self.toc = get_nb_toc(page.file.abs_src_path)

            # replace render with new_render for this object only
            page.render = new_render.__get__(page, Page)

            # Add metadata for template
            self._set_nb_url(page)
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


def get_nb_toc(fpath):
    """Returns a TOC for the Notebook
    It does that by converting first to MD
    """
    body = convert.nb2md(fpath)
    md_toc_tokens = get_markdown_toc(body)
    toc = get_toc(md_toc_tokens)
    return toc
