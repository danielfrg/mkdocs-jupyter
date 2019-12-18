import os
import re
import yaml
from copy import deepcopy

import jinja2
from pygments.formatters import HtmlFormatter

import IPython
from traitlets import Integer
from traitlets.config import Config

from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import Preprocessor, CSSHTMLHeaderPreprocessor

from nbconvert.filters.highlight import _pygments_highlight
from nbconvert.nbconvertapp import NbConvertApp

from .templates import LATEX_CUSTOM_SCRIPT, GENERATED_MD


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def convert(nb_path):
    """Convert a notebook to html with css included and fixes
    """
    html = nb2html(nb_path)
    print("Converted: {nb_path}".format(nb_path=nb_path))
    return GENERATED_MD.format(html=html)


def get_metadata(nb_path):
    """Read the .nbdata file associated with a notebook and return the metadata"""
    filedir = os.path.dirname(nb_path)
    filename = os.path.basename(nb_path)
    metadata_filename = os.path.splitext(filename)[0] + '.yml'
    metadata_filepath = os.path.join(filedir, metadata_filename)

    if not os.path.exists(metadata_filepath):
        print("No .yml file found for {f}".format(f=nb_path))
        return

    with open(os.path.join(filedir, metadata_filename), "r") as f:
        try:
            return yaml.load(f)
        except yaml.YAMLError as exc:
            print(exc)


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


def nb2html(nb_path):
    """Convert a notebook and return html"""
    template = os.path.join(THIS_DIR, "assets", "notebook.tpl")

    content, info = get_html_from_filepath(nb_path, template=template)

    # Fix CSS
    html = generate_html(content, info, fix_css=True, ignore_css=False)
    return html


def get_html_from_filepath(filepath,
                           start=0,
                           end=None,
                           template=None):
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
    })

    # Overwrite Custom jinja filters
    # This is broken right now so needs fix from below
    # https://github.com/jupyter/nbconvert/pull/877
    filters = {
        "highlight_code": custom_highlight_code
    }

    exporter = HTMLExporter(
        config=app.config,
        template_file=template_file,
        extra_loaders=extra_loaders,
        filters=filters,
        preprocessors=preprocessors_,
    )
    content, info = exporter.from_filename(filepath)

    # Fix for nbconvert bug
    # content = content.replace("<pre>", '<pre class="highlight highlight-ipynb">')
    # end-fix

    # Since we make a Markdown file we need to remove empty lines and strip
    content = "\n".join([line.rstrip() for line in content.split("\n") if line.rstrip()])

    return content, info


def custom_highlight_code(source, language="python", metadata=None):
    """
    Makes the syntax highlighting from pygments in the Notebook output
    have the prefix(`highlight-ipynb`).
    So it doesn"t break the theme pygments
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
        We try to get only the Jupyter Notebook CSS without the extra stuff.
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
