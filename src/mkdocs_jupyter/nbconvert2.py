"""
This modules is a wrapper around nbconvert
It provides a cleaner / more self-contained version of the HTML content
that can be embedded into existing HTML pages without breaking existing styles
"""

import base64
import hashlib
import io
import json
import logging
import os
import re
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

import jupytext
import mistune
from defusedxml import ElementTree
from jinja2 import FileSystemLoader, pass_context
from nbconvert.exporters.html import HTMLExporter
from nbconvert.exporters.markdown import MarkdownExporter
from nbconvert.exporters.templateexporter import default_filters
from nbconvert.filters.highlight import _pygments_highlight
from nbconvert.filters.markdown_mistune import IPythonRenderer, MarkdownWithMath
from nbconvert.nbconvertapp import NbConvertApp
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from mkdocs_jupyter.config import settings
from mkdocs_jupyter.exporter_options import (
    MANAGED_OPTIONS,
    validate_html_exporter_options,
)
from mkdocs_jupyter.metadata import NotebookMetadataMixin
from mkdocs_jupyter.mathjax import (
    DEFAULT_MATHJAX_URL as DEFAULT_MATHJAX_URL,
    mathjax_script,
    mathjax_url,
    normalize_latex_output,
)
from mkdocs_jupyter.preprocessors import SubCell

logger = logging.getLogger("mkdocs.mkdocs-jupyter")

# Language of the kernel (used for syntax highlighting)
kernel_lang = "python"

# We use this to tag each div with code with an unique ID for the copy-to-clipboard
cell_id = 0


class NotebookHTMLExporter(NotebookMetadataMixin, HTMLExporter):
    """HTML export without the notebook's page frontmatter."""

    @pass_context
    def markdown2html(self, context, source):
        legacy_math = (
            context.get("resources", {}).get("mkdocs", {}).get("mathjax_version", 4)
            == 2
        )
        if legacy_math and not self.embed_images:
            return super().markdown2html(context, source)
        cell = context.get("cell", {})
        renderer_class = ImageDependencyRenderer if legacy_math else ModernMathRenderer
        renderer = renderer_class(
            escape=False,
            attachments=cell.get("attachments", {}),
            embed_images=self.embed_images,
            image_dependencies=getattr(self, "_image_dependencies", None),
            path=context.get("resources", {}).get("metadata", {}).get("path", ""),
            anchor_link_text=self.anchor_link_text,
            exclude_anchor_links=self.exclude_anchor_links,
        )
        return MarkdownWithMath(renderer=renderer).render(source)


class ImageDependencyRenderer(IPythonRenderer):
    """Record the exact local bytes embedded by nbconvert's image renderer."""

    def __init__(self, *args, image_dependencies=None, **kwargs):
        self.image_dependencies = image_dependencies
        super().__init__(*args, **kwargs)

    def _src_to_base64(self, src):
        embedded = super()._src_to_base64(src)
        if self.image_dependencies is None:
            return embedded
        # Keep the lookup path so replacing a symlink also invalidates the cache.
        if embedded is None:
            try:
                scheme = urlsplit(src).scheme
            except ValueError:
                return embedded
            if (scheme and not os.path.isabs(src)) or src.startswith("//"):
                return embedded
        path = os.path.abspath(os.path.join(self.path, src))
        digest = (
            hashlib.sha256(base64.b64decode(embedded.split(",", 1)[1])).hexdigest()
            if embedded is not None
            else None
        )
        self.image_dependencies[path] = digest
        return embedded


class ModernMathRenderer(ImageDependencyRenderer):
    """Emit explicit math regions compatible with site-owned arithmatex setups."""

    def inline_math(self, body):
        return '<span class="arithmatex">\\(' + self.escape_html(body) + "\\)</span>"

    def block_math(self, body):
        return '<div class="arithmatex">\\[' + self.escape_html(body) + "\\]</div>"

    def latex_environment(self, name, body):
        return (
            '<div class="arithmatex">'
            + super().latex_environment(name, body)
            + "</div>"
        )


class NotebookMarkdownExporter(NotebookMetadataMixin, MarkdownExporter):
    """TOC export without the notebook's page frontmatter."""


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
    no_prompt: bool = False,
    remove_tag_config: dict = {},
    highlight_extra_classes: str = "",
    include_requirejs: bool = False,
    custom_mathjax_url: str = "",
    include_mermaidjs: bool = True,
    custom_template: str | None = None,
    mathjax_version: int = 4,
    include_mathjax: bool = True,
    html_exporter_options: dict | None = None,
    image_dependencies: dict | None = None,
    markdown_cell_processor: str = "jupyter",
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
        no_prompt: bool
            Render notebook without input or output prompts (default: False)
        remove_tag_config: dict
            Configure rendering based on cell tags (default: {})
    Returns
    -------
        HTML content
    """
    exporter_options = validate_html_exporter_options(html_exporter_options)
    if markdown_cell_processor not in ("jupyter", "mkdocs"):
        raise ValueError("markdown_cell_processor must be jupyter or mkdocs")
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
        no_prompt=no_prompt,
        remove_tag_config=remove_tag_config,
    )

    # Use the templates included in this package
    template_file = "mkdocs_html/notebook.html.j2"
    extra_template_paths = [settings.templates_dir]
    template_options = {}
    if custom_template:
        template_path = Path(custom_template).absolute()
        if not template_path.is_file():
            raise FileNotFoundError(
                f"Custom notebook template not found: {template_path}"
            )
        template_file = template_path.name
        template_options["extra_loaders"] = [FileSystemLoader(template_path.parent)]

    # Customize NBConvert App
    preprocessors_ = [SubCell]
    filters = {
        "highlight_code": mk_custom_highlight_code(
            extra_css_classes=highlight_extra_classes
        ),
        "normalize_latex_output": normalize_latex_output,
    }

    # Ensures SVG rendered with data and rdkit exit with NOOP
    # Source: https://github.com/jupyter/nbconvert/issues/1894#issuecomment-1334355109
    def custom_clean_html(element):
        return element.decode() if isinstance(element, bytes) else str(element)

    default_filters["clean_html"] = custom_clean_html

    # Dedicated plugin settings and package-owned templates take precedence.
    options = {
        name: value
        for name, value in exporter_options.items()
        if name not in MANAGED_OPTIONS
    }
    if exporter_options:
        options["exclude_input"] = no_input or not show_input
        if no_input or no_prompt:
            options["exclude_input_prompt"] = True
            options["exclude_output_prompt"] = True
    exporter = NotebookHTMLExporter(
        **options,
        config=app.config,
        template_file=template_file,
        extra_template_paths=extra_template_paths,
        preprocessors=preprocessors_,
        filters=filters,
        theme=theme,
        mathjax_url=mathjax_url(mathjax_version, custom_mathjax_url),
        **template_options,
    )
    exporter._image_dependencies = image_dependencies
    if custom_template:
        # nbconvert's binary asset fallback uses paths rather than Jinja loaders.
        exporter.template_paths = [str(template_path.parent), *exporter.template_paths]

    resources = {
        "metadata": {"path": os.path.dirname(os.path.abspath(nb_path))},
        "mkdocs": {
            "markdown_cell_processor": markdown_cell_processor,
            "include_requirejs": include_requirejs,
            "include_mermaidjs": include_mermaidjs,
            "mathjax_version": mathjax_version,
            "mathjax_script": (
                mathjax_script(mathjax_version, custom_mathjax_url)
                if include_mathjax and mathjax_version != 2
                else ""
            ),
        },
    }
    _, extension = os.path.splitext(nb_path)

    if extension in (".py", ".md"):
        nb = jupytext.read(nb_path)
        nb_file = io.StringIO(jupytext.writes(nb, fmt="ipynb"))
        content, resources = exporter.from_file(nb_file, resources=resources)
    else:
        try:
            with open(nb_path, "r", encoding="utf-8") as f:
                nb_json = json.load(f)
                kernel_lang = nb_json["metadata"]["kernelspec"]["language"]
        except KeyError:
            pass
        content, resources = exporter.from_filename(nb_path, resources=resources)
        content = (
            content
            + f"""
        <style>
        {resources["inlining"]["css"]}
        </style>
        """
        )

    if highlight_extra_classes:
        content = content.replace(
            "jp-OutputArea-output",
            f"jp-OutputArea-output {highlight_extra_classes}",
        )

    return content


def _extract_toc_headings(source):
    """Extract one cell's headings using the notebook HTML Markdown parser."""
    headings = []

    class HeadingRenderer(IPythonRenderer):
        def heading(self, text, level, **attrs):
            html = super().heading(text, level)
            try:
                heading = ElementTree.fromstring(html)
            except Exception:
                # The HTML exporter also omits anchors for invalid heading HTML.
                return ""
            heading_id = heading.get("id")
            if heading_id is not None:
                # Preserve literal visible text and the HTML exporter's exact ID.
                heading.remove(heading[-1])
                label = "".join(heading.itertext()).replace("\n", " ")
                label = escape(label, quote=False)
                label = re.sub(r"([\\`*_{}\[\]()#+.!>-])", r"\\\1", label)
                headings.append(f"{'#' * level} {label} {{#{heading_id}}}\n")
            return ""

    MarkdownWithMath(renderer=HeadingRenderer(escape=False)).render(source)
    return "\n".join(headings)


def nb2md(nb_path, start=0, end=None, execute=False, kernel_name=""):
    """Extract notebook headings as Markdown for the MkDocs table of contents.

    The template omits code cells and parses each Markdown cell independently
    using the same parser as HTML export, retaining only its actual headings.
    """

    app = get_nbconvert_app(
        start=start, end=end, execute=execute, kernel_name=kernel_name
    )

    # Use the templates included in this package
    template_file = "mkdocs_md/md-no-codecell.md.j2"
    extra_template_paths = [settings.templates_dir]

    exporter = NotebookMarkdownExporter(
        config=app.config,
        template_file=template_file,
        extra_template_paths=extra_template_paths,
        filters={"extract_toc_headings": _extract_toc_headings},
    )

    _, extension = os.path.splitext(nb_path)

    if extension in (".py", ".md"):
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
    no_prompt: bool = False,
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

    if no_prompt:
        template_exported_conf["TemplateExporter"].update(
            {
                "exclude_output_prompt": True,
                "exclude_input_prompt": True,
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

        escaped = mistune.escape(source)
        clipboard_copy_txt = f"""<div id="cell-{cell_id}" class="clipboard-copy-txt">{escaped}</div>
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
    return MarkdownWithMath(renderer=CustomMarkdownRendered(escape=False)).render(
        source
    )


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
