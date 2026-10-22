"""MkDocs processing for notebook Markdown cells."""

import json
from copy import deepcopy
from html.parser import HTMLParser

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

try:
    from mkdocs.utils.rendering import get_heading_text
except ImportError:  # MkDocs 1.4 does not provide the rendering helper.
    def get_heading_text(heading, md):
        heading = deepcopy(heading)
        if len(heading) and heading[-1].get("class") == "headerlink":
            heading.remove(heading[-1])
        md.treeprocessors["unescape"].run(heading)

        class Text(HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts = []

            def handle_data(self, data):
                self.parts.append(data)

            def handle_starttag(self, tag, attrs):
                if tag == "img":
                    self.parts.append(dict(attrs).get("alt", ""))

        source = md.serializer(heading)
        for postprocessor in md.postprocessors:
            source = postprocessor.run(source)
        parser = Text()
        parser.feed(source)
        return " ".join("".join(parser.parts).split())


class NotebookMarkdownExtension(Extension):
    def __init__(self, page, set_title):
        self.page = page
        self.set_title = set_title
        super().__init__()

    def extendMarkdown(self, md):
        md.treeprocessors.register(
            NotebookCells(md, self.page, self.set_title), "notebook_cells", 2
        )


class NotebookCells(Treeprocessor):
    def __init__(self, md, page, set_title):
        super().__init__(md)
        self.page = page
        self.set_title = set_title

    def run(self, root):
        title = None
        for cell in root.iter("div"):
            if "jp-MarkdownCell" not in cell.get("class", "").split():
                continue
            attachments = json.loads(
                cell.attrib.pop("data-mkdocs-jupyter-attachments", "{}")
            )
            for image in cell.iter("img"):
                source = image.get("src", "")
                if source.startswith("attachment:"):
                    data = attachments.get(source[len("attachment:"):])
                    if data:
                        preferred = ("image/svg+xml", "image/png", "image/jpeg")
                        mime = next(
                            (kind for kind in preferred if kind in data),
                            next(iter(data)),
                        )
                        image.set("src", f"data:{mime};base64,{data[mime]}")
            if title is None:
                heading = next(cell.iter("h1"), None)
                if heading is not None:
                    title = get_heading_text(heading, self.md)
        if title is not None and self.set_title:
            self.page.title = title
