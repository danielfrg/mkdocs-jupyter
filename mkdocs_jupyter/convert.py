import os
import re
import yaml
import unicodedata
from copy import deepcopy

import jinja2
from pygments.formatters import HtmlFormatter

import IPython
from traitlets import Integer
from traitlets.config import Config

from nbconvert.exporters import HTMLExporter, MarkdownExporter
from nbconvert.preprocessors import Preprocessor, CSSHTMLHeaderPreprocessor
from nbconvert.preprocessors import ExecutePreprocessor

from nbconvert.filters.highlight import _pygments_highlight
from nbconvert.nbconvertapp import NbConvertApp

from .utils import slugify
from .templates import LATEX_CUSTOM_SCRIPT, GENERATED_MD

# We monkeypath nbconvert.filters.markdown_mistune.IPythonRenderer.header
# To use a version that makes the id all lowercase
# because mkdocs uses just lowercase on the TOC to make it url friendly
# So this makes the links from the TOC work

from nbconvert.filters.markdown_mistune import IPythonRenderer


def add_anchor_lower_id(html, anchor_link_text=u'¶'):
    from ipython_genutils import py3compat
    from defusedxml import cElementTree as ElementTree
    from xml.etree.cElementTree import Element
    from nbconvert.filters.strings import _convert_header_id, html2text

    try:
        h = ElementTree.fromstring(py3compat.cast_bytes_py2(html, encoding='utf-8'))
    except Exception:
        # failed to parse, just return it unmodified
        return html
    link = _convert_header_id(html2text(h))
    h.set("id", slugify(link))
    a = Element("a", {"class": "anchor-link", "href": "#" + link})
    try:
        # Test if the anchor link text is HTML (e.g. an image)
        a.append(ElementTree.fromstring(anchor_link_text))
    except Exception:
        # If we fail to parse, assume we've just got regular text
        a.text = anchor_link_text
    h.append(a)

    # Known issue of Python3.x, ElementTree.tostring() returns a byte string
    # instead of a text string.  See issue http://bugs.python.org/issue10942
    # Workaround is to make sure the bytes are casted to a string.
    return py3compat.decode(ElementTree.tostring(h), 'utf-8')


def new_header(self, text, level, raw=None):
    html = super(IPythonRenderer, self).header(text, level, raw=raw)
    anchor_link_text = self.options.get('anchor_link_text', u'¶')
    return add_anchor_lower_id(html, anchor_link_text=anchor_link_text)

IPythonRenderer.header = new_header

## End monkeypath


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def nb2html(nb_path, execute=False):
    """Convert a notebook and return html"""
    template = os.path.join(THIS_DIR, "assets", "notebook.tpl")
    content, info = get_html_from_filepath(nb_path, template=template, execute=execute)

    # Fix CSS
    html = generate_html(content, info, fix_css=True, ignore_css=False)
    return GENERATED_MD.format(html=html)


def nb2md(nb_path):
    """Convert a notebook and return markdown

    We use a template that removed all code cells because if the body
    is to big (javascript and stuff) it takes to long to read and parse
    """
    config = Config()
    template = os.path.join(THIS_DIR, "assets", "md-no-codecell.tpl")
    template_file = os.path.basename(template)
    extra_loaders = []
    extra_loaders.append(jinja2.FileSystemLoader([os.path.dirname(template)]))

    exporter = MarkdownExporter(
        config=config,
        template_file=template_file,
        extra_loaders=extra_loaders,
        # filters=filters,
        # preprocessors=preprocessors_,
    )

    body, resources = exporter.from_filename(nb_path)
    return body


class SliceIndex(Integer):
    """An integer trait that accepts None"""

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
        nbc.cells = nbc.cells[self.start:self.end]
        return nbc, resources


def get_html_from_filepath(filepath, start=0, end=None, template=None, execute=False):
    """Return the HTML from a Jupyter Notebook
    """
    preprocessors_ = [SubCell]

    template_file = "basic"
    extra_loaders = []
    if template:
        extra_loaders.append(
            jinja2.FileSystemLoader([os.path.dirname(template)]))
        template_file = os.path.basename(template)

    # Load the user's nbconvert configuration
    app = NbConvertApp()
    app.load_config_file()

    app.config.update({
        # This Preprocessor changes the pygments css prefixes
        # from .highlight to .highlight-ipynb
        "CSSHTMLHeaderPreprocessor": {
            "enabled": True,
            "highlight_class": ".highlight-ipynb",
        },
        "SubCell": {
            "enabled": True,
            "start": start,
            "end": end
        },
        # "ExecutePreprocessor": {
        #     "enabled": execute,
        #     "store_widget_state": True
        # }
    })

    # Overwrite Custom jinja filters
    # This is broken right now so needs fix from below
    # https://github.com/jupyter/nbconvert/pull/877
    # TODO: is this fixed and released?
    filters = {
        "highlight_code": custom_highlight_code,
    }

    exporter = HTMLExporter(
        config=app.config,
        template_file=template_file,
        preprocessors=preprocessors_,
        extra_loaders=extra_loaders,
        filters=filters,
    )
    content, info = exporter.from_filename(filepath)

    return content, info


def custom_highlight_code(source, language="python", metadata=None):
    """
    Makes the syntax highlighting from pygments in the Notebook output
    have the prefix(`highlight-ipynb`).
    So it doesn't break the theme pygments
    This modifies only html content, not css
    """
    if not language:
        language = "ipython3"

    formatter = HtmlFormatter(cssclass=" highlight highlight-ipynb hl-"+language)
    output = _pygments_highlight(source, formatter, language, metadata)
    return output


def generate_html(content, info, fix_css=True, ignore_css=False):
    """
    General fixes for the notebook generated html
    fix_css is to do a basic filter to remove extra CSS from the Jupyter CSS
    ignore_css is to not include at all the Jupyter CSS
    """

    def style_tag(styles):
        return '<style type="text/css">{0}</style>'.format(styles)

    def filter_css(style):
        """
        This is a little bit of a Hack.
        Jupyter returns a lot of CSS including its own bootstrap.
        We try to get only the Jupyter Notebook CSS without the base stuff
        so the site theme doesn't break
        """
        index = style.find("/*!\n*\n* IPython notebook\n*\n*/")
        if index > 0:
            style = style[index:]
        index = style.find("/*!\n*\n* IPython notebook webapp\n*\n*/")
        if index > 0:
            style = style[:index]

        style = re.sub(r"color\:\#0+(;)?", "", style)
        style = re.sub(r"\.rendered_html[a-z0-9,._ ]*\{[a-z0-9:;%.#\-\s\n]+\}",
                       "", style)
        return style_tag(style)

    if not ignore_css:
        jupyter_css = "\n".join(
            style_tag(style) for style in info["inlining"]["css"])
        if fix_css:
            jupyter_css = "\n".join(
                filter_css(style) for style in info["inlining"]["css"])
        content = jupyter_css + content
    content = content + LATEX_CUSTOM_SCRIPT
    return content
