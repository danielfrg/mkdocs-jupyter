"""
This modules is a wrapper around nbconvert
It provides a cleaner / more self-contained version of the HTML content
that can be embedded into existing HTML pages without breaking existing styles
"""

import io
import json
import logging
import os

import jupytext
import mistune
from nbconvert.exporters.html import HTMLExporter
from nbconvert.exporters.markdown import MarkdownExporter
from nbconvert.exporters.templateexporter import default_filters
from nbconvert.filters.highlight import _pygments_highlight
from nbconvert.filters.markdown_mistune import (
    IPythonRenderer,
    MarkdownWithMath,
)
from nbconvert.nbconvertapp import NbConvertApp
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from mkdocs_jupyter.config import settings
from mkdocs_jupyter.preprocessors import SubCell

logger = logging.getLogger("mkdocs.mkdocs-jupyter")

# Language of the kernel (used for syntax highlighting)
kernel_lang = "python"

# We use this to tag each div with code with an unique ID for the copy-to-clipboard
cell_id = 0


def nb2html(
    nb_path,
    execute=False,
    kernel_name="",
    theme="light",
    start=0,
    end=None,
    allow_errors=True,
    show_input: bool = True,
    no_input: bool = False,
    remove_tag_config: dict = {},
    highlight_extra_classes: str = "",
    include_requirejs: bool = False,
):
    """
    Convert a notebook to HTML

    Arguments
    ---------
        nb_path: str
            Path to the notebook
        execute: bool
            Whether to execute the notebook
        kernel_name: str
            Name of the kernel to use
        theme: str
            Name of the theme to use (default: light) (options: light or dark)
        start: int
            Start cell number
        end: int
            End cell number
        allow_errors
            Render even if notebook execution fails
        show_input: bool
            Shows code input (default: True)
        no_input: bool
            Render notebook without code or output (default: False)
        remove_tag_config: dict
            Configure rendering based on cell tags (default: {})
    Returns
    -------
        HTML content
    """
    logger.info(f"Converting notebook (execute={execute}): {nb_path}")

    global cell_id, kernel_lang
    cell_id = 0  # Reset the cell id

    app = get_nbconvert_app(
        execute=execute,
        kernel_name=kernel_name,
        start=start,
        end=end,
        allow_errors=allow_errors,
        show_input=show_input,
        no_input=no_input,
        remove_tag_config=remove_tag_config,
    )

    # Use the templates included in this package
    template_file = "mkdocs_html/notebook.html.j2"
    extra_template_paths = [settings.templates_dir]

    # Customize NBConvert App
    preprocessors_ = [SubCell]
    filters = {
        "highlight_code": mk_custom_highlight_code(
            extra_css_classes=highlight_extra_classes
        ),
        # "markdown2html": custom_markdown2html,
    }

    # Ensures SVG rendered with data and rdkit exit with NOOP
    # Source: https://github.com/jupyter/nbconvert/issues/1894#issuecomment-1334355109
    def custom_clean_html(element):
        return element.decode() if isinstance(element, bytes) else str(element)

    default_filters["clean_html"] = custom_clean_html

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
        content, resources = exporter.from_file(
            nb_file,
            resources={
                "mkdocs": {
                    "test": "value",
                    "include_requirejs": include_requirejs,
                }
            },
        )
    else:
        try:
            with open(nb_path, "r", encoding="utf-8") as f:
                nb_json = json.load(f)
                kernel_lang = nb_json["metadata"]["kernelspec"]["language"]
        except KeyError:
            pass
        content, resources = exporter.from_filename(
            nb_path,
            resources={
                "mkdocs": {
                    "test": "value",
                    "include_requirejs": include_requirejs,
                }
            },
        )
        content = content + f"""
        <style>
        {resources["inlining"]["css"]}
        </style>
        """

    if highlight_extra_classes:
        content = content.replace(
            "jp-OutputArea-output",
            f"jp-OutputArea-output {highlight_extra_classes}",
        )

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
    extra_template_paths = [settings.templates_dir]

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


def get_nbconvert_app(
    execute=False,
    kernel_name="",
    start=0,
    end=None,
    allow_errors=True,
    show_input: bool = True,
    no_input: bool = False,
    remove_tag_config: dict = {},
) -> NbConvertApp:
    """Create"""

    # Load the user's nbconvert configuration
    app = NbConvertApp()
    app.load_config_file()

    template_exported_conf = {
        "TemplateExporter": {
            "exclude_input": not show_input,
        }
    }

    if no_input:
        template_exported_conf.update(
            {
                "TemplateExporter": {
                    "exclude_output_prompt": True,
                    "exclude_input": True,
                    "exclude_input_prompt": True,
                }
            }
        )

    if remove_tag_config != {}:
        template_exported_conf.update(
            {
                "TagRemovePreprocessor": {
                    "enabled": True,
                }
            }
        )
        for conf_param, conf_value in remove_tag_config.items():
            if conf_param in [
                "remove_cell_tags",
                "remove_all_outputs_tags",
                "remove_single_output_tags",
                "remove_input_tags",
            ]:
                template_exported_conf["TagRemovePreprocessor"].update(
                    {
                        conf_param: {conf_value[0]},
                    }
                )

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
                "allow_errors": allow_errors,
            },
            **template_exported_conf,
        }
    )

    return app


def mk_custom_highlight_code(extra_css_classes=""):
    def custom_highlight_code(source, language=None, metadata=None):
        """
        Change CSS class names from .highlight to .highlight-ipynb.
        These are the <div> that contains the <pre>

        This modifies only the HTML not CSS.
        On the `notebook.html.js` template we modify the CSS styles.
        """
        global cell_id
        cell_id = cell_id + 1
        if not language:
            language = kernel_lang

        classes = f"highlight-ipynb hl-{language} {extra_css_classes}"
        formatter = HtmlFormatter(cssclass=classes)
        output = _pygments_highlight(source, formatter, language, metadata)

        clipboard_copy_txt = f"""<div id="cell-{cell_id}" class="clipboard-copy-txt">{source}</div>
        """
        return output + clipboard_copy_txt

    return custom_highlight_code


def custom_markdown2html(source):
    """
    This filter uses a Custom Rendered that uses a custom CodeHtmlFormatter
    to wrap the language blocks into a <div> and a <pre> tags.
    This is done so it's the same HTML structure that for regular non-language
    sections.
    """
    return MarkdownWithMath(
        renderer=CustomMarkdownRendered(escape=False)
    ).render(source)


class CustomMarkdownRendered(IPythonRenderer):
    def block_code(self, code, lang):
        lexer = None
        if lang:
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except ClassNotFound:
                code = lang + "\n" + code
                lang = None

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
    content = nb2html("./demo/docs/demo-nb.ipynb", theme="light")
    with open("./demo.html", "w") as f:
        f.write(content)
