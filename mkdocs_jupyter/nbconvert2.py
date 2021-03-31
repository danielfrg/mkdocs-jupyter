"""
This modules is a Wrapper around nbconvert
It provides a cleaner version of the HTML content that can be embeded into other websites.
"""
import io
import logging
import os
from copy import deepcopy

import jupytext
from traitlets import Integer
from pygments.formatters import HtmlFormatter
from nbconvert.exporters import HTMLExporter, MarkdownExporter
from nbconvert.filters.highlight import _pygments_highlight
from nbconvert.nbconvertapp import NbConvertApp
from nbconvert.preprocessors import Preprocessor

from mkdocs_jupyter.templates import GENERATED_MD

# ---
# Variables
logger = logging.getLogger("mkdocs.mkdocs-jupyter")
# ---

THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def nb2html(nb_path, start=0, end=None, execute=False, kernel_name=""):
    """Convert a notebook and return html"""
    logger.info(f"Converting notebook: {nb_path}")

    app = get_nbconvert_app(
        start=start, end=end, execute=execute, kernel_name=kernel_name
    )

    # Use the templates included in this package
    template_file = "mkdocs_html/notebook.html.j2"
    extra_template_paths = [os.path.join(THIS_DIR, "templates")]

    # Customize NBConvert App
    preprocessors_ = [SubCell]
    filters = {
        "highlight_code": custom_highlight_code,
    }

    exporter = HTMLExporter(
        config=app.config,
        template_file=template_file,
        extra_template_paths=extra_template_paths,
        preprocessors=preprocessors_,
        filters=filters,
    )

    _, extension = os.path.splitext(nb_path)

    if extension == ".py":
        nb = jupytext.read(nb_path)
        nb_file = io.StringIO(jupytext.writes(nb, fmt="ipynb"))
        html, info = exporter.from_file(nb_file)
    else:
        html, info = exporter.from_filename(nb_path)

    return GENERATED_MD.format(html=html)


def nb2md(nb_path, start=0, end=None, execute=False, kernel_name=""):
    """Convert a notebook to markdown

    We use a template that removed all code cells because if the body
    is to big ( with javascript and CSS) it takes to long to read and parse
    """

    app = get_nbconvert_app(
        start=start, end=end, execute=execute, kernel_name=kernel_name
    )

    # Use the templates included in this package
    template_file = "mkdocs_md/md-no-codecell.md.j2"
    extra_template_paths = [os.path.join(THIS_DIR, "templates")]

    exporter = MarkdownExporter(
        config=app.config,
        template_file=template_file,
        extra_template_paths=extra_template_paths,
    )

    _, extension = os.path.splitext(nb_path)

    if extension == ".py":
        nb = jupytext.read(nb_path)
        nb_file = io.StringIO(jupytext.writes(nb, fmt="ipynb"))
        body, resources = exporter.from_file(nb_file)
    else:
        body, resources = exporter.from_filename(nb_path)
    return body


def get_nbconvert_app(start=0, end=None, execute=False, kernel_name=""):
    # Load the user's nbconvert configuration
    app = NbConvertApp()
    app.load_config_file()

    app.config.update(
        {
            # This Preprocessor changes the pygments css prefixes
            # from .highlight to .highlight-ipynb
            "CSSHTMLHeaderPreprocessor": {
                "enabled": True,
                "highlight_class": ".highlight-ipynb",
            },
            "SubCell": {"enabled": True, "start": start, "end": end},
            "ExecutePreprocessor": {
                "enabled": execute,
                "store_widget_state": True,
                "kernel_name": kernel_name,
            },
        }
    )

    return app


class SliceIndex(Integer):
    """An integer trait that accepts None
    Used by the SubCell Preprocessor"""

    default_value = None

    def validate(self, obj, value):
        if value is None:
            return value
        else:
            return super(SliceIndex, self).validate(obj, value)


class SubCell(Preprocessor):
    """A preprocessor to select a slice of the cells of a notebook"""

    start = SliceIndex(0, config=True, help="First cell of notebook")
    end = SliceIndex(None, config=True, help="Last cell of notebook")

    def preprocess(self, nb, resources):
        nbc = deepcopy(nb)
        nbc.cells = nbc.cells[self.start : self.end]
        return nbc, resources


def custom_highlight_code(source, language="python", metadata=None):
    """
    Makes the class of the div that contains the `<pre>`
    be `highlight-ipynb` instaed of `highlight`.

    So it doesn't break the website theme
    This modifies only html content, not CSS
    On the notebook.html.js we modify this
    """
    if not language:
        language = "python"

    formatter = HtmlFormatter(cssclass="highlight-ipynb hl-" + language)
    output = _pygments_highlight(source, formatter, language, metadata)
    return output


if __name__ == "__main__":
    nb2html("tests/mkdocs/docs/demo.ipynb")
