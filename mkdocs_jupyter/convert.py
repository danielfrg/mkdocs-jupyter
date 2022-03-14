from nbconvert.filters.markdown_mistune import IPythonRenderer

from mkdocs_jupyter.utils import slugify

# ------------------------------------------------------------------------------
# This makes the links from the TOC work
# We monkeypatch nbconvert.filters.markdown_mistune.IPythonRenderer.header
# to use a version that makes the id all lowercase
# We do this because mkdocs uses all lowercase TOC titles
# (to make them url-friendly)


def add_anchor_lower_id(html, anchor_link_text="¶"):
    from xml.etree.cElementTree import Element

    from defusedxml import cElementTree as ElementTree
    from nbconvert.filters.strings import _convert_header_id, html2text

    try:
        h = ElementTree.fromstring(html)
    except Exception:
        # failed to parse, just return it unmodified
        return html
    link = _convert_header_id(slugify(html2text(h)))
    h.set("id", link)
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
    return ElementTree.tostring(h).decode("utf-8", "replace")


def new_header(self, text, level, raw=None):
    html = super(IPythonRenderer, self).header(text, level, raw=raw)
    anchor_link_text = self.options.get("anchor_link_text", "¶")
    return add_anchor_lower_id(html, anchor_link_text=anchor_link_text)


IPythonRenderer.header = new_header

# End monkeypatch --------------------------------------------------------------

from .nbconvert2 import *
