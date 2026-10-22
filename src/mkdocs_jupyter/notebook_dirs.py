"""Mount notebook source directories without copying them into docs_dir."""

import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import unquote, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from mkdocs.exceptions import ConfigurationError, PluginError
from mkdocs.structure.files import File
from mkdocs.utils import get_relative_url


def configure_notebook_dirs(mapping, config):
    if not mapping:
        return []
    base = Path(config["config_file_path"]).parent
    site = Path(config["site_dir"]).resolve()
    mounts = []
    for mount, directory in mapping.items():
        if (
            not isinstance(mount, str)
            or not mount
            or "\\" in mount
            or PurePosixPath(mount).is_absolute()
            or PureWindowsPath(mount).drive
            or ".." in PurePosixPath(mount).parts
            or not PurePosixPath(mount).parts
        ):
            raise ConfigurationError(
                "notebook_dirs mount paths must be nonempty relative paths "
                f"without '..': {mount!r}"
            )
        if not isinstance(directory, str) or not directory.strip():
            raise ConfigurationError(
                f"notebook_dirs source for {mount!r} must be a directory path."
            )
        source = (base / directory).resolve()
        if not source.is_dir():
            raise ConfigurationError(
                f"notebook_dirs directory does not exist: {source}"
            )
        if source == site or site in source.parents:
            raise ConfigurationError(
                f"notebook_dirs directory cannot be inside site_dir: {source}"
            )
        prefix = PurePosixPath(mount).as_posix()
        mounts.append((prefix, source))
        if str(source) not in config["watch"]:
            config["watch"].append(str(source))
    return mounts


def external_files(mounts, config, cache_dir):
    excluded = {Path(config["site_dir"]).resolve(), Path(cache_dir).resolve()}
    result = []
    for mount, source in mounts:
        for folder, directories, filenames in os.walk(source, followlinks=False):
            directories[:] = sorted(
                name
                for name in directories
                if not name.startswith(".")
                and (Path(folder) / name).resolve() not in excluded
                and (Path(folder) / name).relative_to(source).as_posix() != "templates"
            )
            for name in sorted(filenames):
                physical = Path(folder) / name
                if name.startswith(".") or not physical.is_file():
                    continue
                path = (PurePosixPath(mount) / physical.relative_to(source)).as_posix()
                file = File(
                    path, str(source), config["site_dir"], config["use_directory_urls"]
                )
                file.abs_src_path = str(physical)
                file.edit_uri = Path(
                    os.path.relpath(physical, config["docs_dir"])
                ).as_posix()
                file._mkdocs_jupyter_mount = mount
                result.append(file)
    # These options were added after the oldest supported MkDocs release.
    try:
        from mkdocs.structure.files import set_exclusions
    except ImportError:
        pass
    else:
        set_exclusions(result, config)
    return result


def check_collisions(files, include_source):
    targets = []
    for file in files:
        inclusion = getattr(file, "inclusion", None)
        if inclusion is not None and inclusion.name == "EXCLUDED":
            continue
        targets.append((Path(file.dest_path).as_posix(), file))
        if include_source and file.is_documentation_page() and hasattr(file, "file"):
            target = (
                PurePosixPath(Path(file.dest_path).as_posix()).parent
                / Path(file.abs_src_path).name
            )
            targets.append((target.as_posix(), file))
    seen = {}
    for target, file in sorted(targets, key=lambda item: item[0]):
        path = PurePosixPath(target)
        for ancestor in (path, *path.parents):
            other = seen.get(ancestor.as_posix())
            if other is not None and (
                getattr(file, "_mkdocs_jupyter_mount", None)
                or getattr(other, "_mkdocs_jupyter_mount", None)
            ):
                raise PluginError(
                    "notebook_dirs output collision: "
                    f"{other.src_path!r} and {file.src_path!r} conflict at {target!r}."
                )
        seen.setdefault(target, file)


def rewrite_notebook_urls(html, current, files, *, markdown_processed=False):
    """Resolve links against real sources, then use their final site URLs."""
    by_source = {}
    for file in files:
        inclusion = getattr(file, "inclusion", None)
        if file.abs_src_path is None or (
            inclusion is not None and inclusion.name == "EXCLUDED"
        ):
            continue
        by_source.setdefault(Path(file.abs_src_path).resolve(), []).append(file)
    source = Path(current.abs_src_path).parent
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        # MkDocs already resolved parsed Markdown links against the virtual
        # documentation paths. Only nbconvert's raw HTML still needs remapping.
        if markdown_processed and tag.find_parent(class_="jp-MarkdownCell"):
            continue
        for attribute in ("href", "src"):
            value = tag.get(attribute)
            if not isinstance(value, str):
                continue
            try:
                url = urlsplit(value)
            except ValueError:
                continue
            if url.scheme or url.netloc or not url.path or url.path.startswith("/"):
                continue
            candidates = by_source.get((source / unquote(url.path)).resolve(), [])
            if not candidates:
                continue
            target = next(
                (
                    file
                    for file in candidates
                    if getattr(file, "_mkdocs_jupyter_mount", None)
                    == current._mkdocs_jupyter_mount
                ),
                candidates[0],
            )
            path = get_relative_url(target.url, current.url)
            tag[attribute] = urlunsplit(("", "", path, url.query, url.fragment))
    return str(soup)
