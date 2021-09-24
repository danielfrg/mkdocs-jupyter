"""
This modules is a wrapper around nbconvert
It provides a cleaner version of the HTML content that can be embedded into existing HTML pages.
"""

import io
import logging
import os
from copy import deepcopy

import jupytext
from nbconvert.exporters import HTMLExporter, MarkdownExporter
from nbconvert.filters.highlight import _pygments_highlight
from nbconvert.nbconvertapp import NbConvertApp
from nbconvert.preprocessors import Preprocessor
from pygments.formatters import HtmlFormatter
from traitlets import Integer


# Variables
logger = logging.getLogger("mkdocs.mkdocs-jupyter")

# END variables


THIS_DIR = os.path.dirname(os.path.realpath(__file__))

cell_id = 0


def nb2html(
    nb_path, start=0, end=None, execute=False, kernel_name="", theme=None
):
    """Convert a notebook

    Returns
    -------
        HTML content
    """
    logger.info(f"Converting notebook (execute={execute}): {nb_path}")

    global cell_id
    cell_id = 0  # Reset this global value

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
        "markdown2html": custom_markdown2html,
    }

    exporter = HTMLExporter(
        config=app.config,
        template_file=template_file,
        extra_template_paths=extra_template_paths,
        preprocessors=preprocessors_,
        filters=filters,
        theme=theme,
    )

    _, extension = os.path.splitext(nb_path)

    if extension == ".py":
        nb = jupytext.read(nb_path)
        nb_file = io.StringIO(jupytext.writes(nb, fmt="ipynb"))
        content, resources = exporter.from_file(nb_file)
    else:
        content, resources = exporter.from_filename(nb_path)

    return content


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
                "allow_errors": True,
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
    Makes the CSS class of the div that contains the `<pre>`
    be `.highlight-ipynb` instead of `.highlight`.

    This modifies only HTML content not CSS
    On the notebook.html.js we modify the CSS styles
    """
    global cell_id
    cell_id = cell_id + 1
    if not language:
        language = "python"

    formatter = HtmlFormatter(cssclass="highlight-ipynb hl-" + language)
    output = _pygments_highlight(source, formatter, language, metadata)

    clipboard_copy_txt = f"""<div id="cell-{cell_id}" class="clipboard-copy-txt">{source}</div>
    """
    return output + clipboard_copy_txt


# This sections creates a new markdown2html filter
# This filter uses a Custom Rendered that uses a custom CodeHtmlFormatter
# All this does is to wrap the language blocks into a div and a pre
# So that it's the same that for regular non-language sections

import mistune
from pygments import highlight
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name
from nbconvert.filters.markdown_mistune import (
    MarkdownWithMath,
    IPythonRenderer,
)


def custom_markdown2html(source):
    return MarkdownWithMath(
        renderer=CustomMarkdownRendered(escape=False)
    ).render(source)


class CustomMarkdownRendered(IPythonRenderer):
    def block_code(self, code, lang):
        if lang:
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except ClassNotFound:
                code = lang + "\n" + code
                lang = None
                lexer = None

        if not lang:
            return "\n<pre><code>%s</code></pre>\n" % mistune.escape(code)

        formatter = CodeHtmlFormatter()
        return highlight(code, lexer, formatter)


class CodeHtmlFormatter(HtmlFormatter):
    def wrap(self, source, outfile):
        return self._wrap_code(source)

    def _wrap_code(self, source):
        yield 0, '<div class="codehilite"><pre><code>'
        for i, t in source:
            yield i, t
        yield 0, "</code></pre></div>"


if __name__ == "__main__":
    content = nb2html("tests/mkdocs/docs/demo.ipynb")
    with open("./demo.html", "w") as f:
        f.write(content)
