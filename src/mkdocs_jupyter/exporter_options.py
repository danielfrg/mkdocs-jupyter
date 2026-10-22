"""Validate exporter options and check dependencies of embedded images."""

import hashlib
from pathlib import Path

from nbconvert.exporters.html import HTMLExporter
from traitlets import TraitError


# These are supplied by the plugin so its rendering pipeline stays intact.
MANAGED_OPTIONS = {
    "template_name",
    "template_file",
    "template_extension",
    "template_paths",
    "extra_template_paths",
    "extra_template_basedirs",
    "filters",
    "preprocessors",
    "default_preprocessors",
    "theme",
    "mathjax_url",
}


def validate_html_exporter_options(options):
    if options is None:
        return {}
    if not isinstance(options, dict):
        raise ValueError(
            "html_exporter_options must be a mapping of option names to values."
        )
    if not options:
        return {}
    traits = HTMLExporter.class_traits(config=True)
    validator = HTMLExporter()
    for name, value in options.items():
        if name not in traits:
            raise ValueError(
                f"Unknown configurable html_exporter_options option: {name!r}"
            )
        try:
            validator.set_trait(name, value)
        except (TraitError, ValueError, TypeError) as error:
            raise ValueError(
                f"Invalid html_exporter_options.{name}: {error}"
            ) from error
    return dict(options)


def image_dependencies_valid(dependencies):
    for path, expected in dependencies.items():
        try:
            actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except FileNotFoundError:
            actual = None
        except OSError:
            return False
        if actual != expected:
            return False
    return True
