"""Page frontmatter shared by MkDocs and notebook exporters."""

import re
from copy import deepcopy
from pathlib import Path

from mkdocs.exceptions import ConfigurationError
from mkdocs.utils import meta


def split_frontmatter(source, source_path="notebook"):
    """Parse a fenced YAML mapping at the start of a Markdown cell."""
    if not re.match(r"^---[ \t]*(?:\r?\n|$)", source):
        return source, None

    # MkDocs requires a newline after the closing fence, including in cells
    # containing only frontmatter. Normalize notebook cell line endings too.
    normalized = source.replace("\r\n", "\n").replace("\r", "\n") + "\n"
    body, metadata = meta.get_data(normalized)
    if body == normalized:
        raise ConfigurationError(
            f"Invalid notebook page metadata in '{source_path}': "
            "expected a closed YAML frontmatter block containing a mapping."
        )
    return body, metadata


def get_notebook_metadata(notebook, source_path):
    """Only the first Markdown cell can supply page metadata."""
    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            return split_frontmatter(cell.source, source_path)[1]
    return None


class NotebookMetadataMixin:
    """Strip page metadata before nbconvert removes, slices or executes cells."""

    def from_notebook_node(self, nb, resources=None, **kwargs):
        resource_metadata = (resources or {}).get("metadata", {})
        source_path = Path(resource_metadata.get("path", "")) / resource_metadata.get(
            "name", "notebook"
        )
        for index, cell in enumerate(nb.cells):
            if cell.cell_type == "markdown":
                body, metadata = split_frontmatter(cell.source, source_path)
                if metadata is not None:
                    nb = deepcopy(nb)
                    nb.cells[index].source = body
                break
        return super().from_notebook_node(nb, resources=resources, **kwargs)
