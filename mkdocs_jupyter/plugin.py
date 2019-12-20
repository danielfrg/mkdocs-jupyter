import os
import markdown

import mkdocs
from mkdocs.structure.toc import get_toc
from mkdocs.structure.pages import Page
from mkdocs.structure.files import Files

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
        ("execute", mkdocs.config.config_options.Type(bool, default=False)),
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

    def on_pre_page(self, page, config, files):
        if str(page.file.abs_src_path).endswith("ipynb"):
            print("Converting:", page.file.abs_src_path)

            exec_nb = self.config["execute"]

            def new_render(self, config, files):
                # print(config)
                body = convert.nb2html(page.file.abs_src_path, execute=exec_nb)
                self.content = body
                self.toc = get_nb_toc(page.file.abs_src_path)

            # replace render with new_render for this object only
            page.render = new_render.__get__(page, Page)
        return page


def get_nb_toc(fpath):
    """Converts the notebook to md and get the toc
    """
    body = convert.nb2md(fpath)

    extensions = ["toc", "fenced_code"]  # config['markdown_extensions']
    mdx_configs = {"toc": {"permalink": True}}  # config['mdx_configs'] or {'toc': {'permalink': True}}
    md = markdown.Markdown(extensions=extensions, extension_configs=mdx_configs)
    content = md.convert(body)

    toc = get_toc(getattr(md, "toc", ""))
    return toc
