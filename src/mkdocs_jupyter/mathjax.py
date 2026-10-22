"""MathJax defaults and the shared, navigation-aware notebook loader."""

import html
import json
import re
from pathlib import Path


MATHJAX_URLS = {
    2: (
        "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/latest.js"
        "?config=TeX-AMS_CHTML-full,Safe"
    ),
    3: "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js",
    4: "https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js",
}
DEFAULT_MATHJAX_URL = MATHJAX_URLS[4]


def mathjax_url(version=4, custom_url=""):
    if type(version) is not int or version not in MATHJAX_URLS:
        raise ValueError("mathjax_version must be 2, 3 or 4")
    return custom_url or MATHJAX_URLS[version]


def mathjax_script(version=4, custom_url=""):
    """Embed the runtime without depending on a site's public asset paths."""
    config = html.escape(
        json.dumps({"url": mathjax_url(version, custom_url), "version": version}),
        quote=True,
    )
    runtime = Path(__file__).with_name("mathjax.js").read_text(encoding="utf-8")
    return f'<script data-mkdocs-jupyter-mathjax="{config}">\n{runtime}\n</script>'


def normalize_latex_output(source):
    """Translate dollar delimiters without changing MIME math regions or prose."""
    tokens = list(
        re.finditer(r"\\begin\{([^}]+)\}|\\end\{[^}]+\}|\\[()\[\]]|\$\$|\$", source)
    )
    closing = {"$": "$", "$$": "$$", "\\(": "\\)", "\\[": "\\]"}

    def unescaped(position):
        preceding = source[:position]
        slashes = len(preceding) - len(preceding.rstrip("\\"))
        return slashes % 2 == 0

    result = []
    consumed = 0
    for index, token in enumerate(tokens):
        if token.start() < consumed or not unescaped(token.start()):
            continue
        delimiter = token.group()
        end_delimiter = closing.get(delimiter)
        if token.group(1) is not None:
            end_delimiter = "\\end{" + token.group(1) + "}"
        if end_delimiter is None:
            continue
        end = next(
            (
                candidate
                for candidate in tokens[index + 1 :]
                if candidate.group() == end_delimiter and unescaped(candidate.start())
            ),
            None,
        )
        if end is None:
            continue
        result.append(source[consumed : token.start()])
        if delimiter in ("$", "$$"):
            left, right = ("\\(", "\\)") if delimiter == "$" else ("\\[", "\\]")
            result.extend([left, source[token.end() : end.start()], right])
        else:
            # Already delimited math and AMS environments keep their TeX intact.
            result.append(source[token.start() : end.end()])
        consumed = end.end()
    result.append(source[consumed:])
    return "".join(result)
