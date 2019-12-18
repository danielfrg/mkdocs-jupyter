import os

import mkdocs
from mkdocs.structure.files import Files

from .convert import convert


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
    )

    def on_files(self, files, config):
        files = Files(
            [
                NotebookFile(f, **config)
                if str(f.abs_src_path).endswith("ipynb")
                else f
                for f in files
            ]
        )
        return files

    def on_page_read_source(self, _, page, config):
        if str(page.file.abs_src_path).endswith("ipynb"):
            body = convert(page.file.abs_src_path)
            return body
        return None
