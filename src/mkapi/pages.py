"""Page class that works with other converter."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import partial
from typing import TYPE_CHECKING

import mkapi.markdown
import mkapi.renderers
from mkapi.globals import resolve_with_attribute
from mkapi.importlib import get_object
from mkapi.objects import Module, is_empty, iter_objects, iter_objects_with_depth
from mkapi.renderers import get_object_filter_for_source
from mkapi.utils import is_module_cache_dirty, split_filters

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


@dataclass
class Page:
    """Page class."""

    name: str
    path: Path
    filters: list[str]
    kind: str
    source: str = field(default="", init=False)
    markdown: str = field(default="", init=False)

    def __post_init__(self) -> None:
        # Delete in MkDocs v1.6. Switch to virtual files
        if not self.path.exists():
            if not self.path.parent.exists():
                self.path.parent.mkdir(parents=True)
            with self.path.open("w") as file:
                file.write("")  # Dummy content

        self.set_markdown()

    def set_markdown(self) -> None:
        """Set markdown."""
        if self.kind == "object":
            self.source = create_object_markdown(self.name, self.path, self.filters)
        elif self.kind == "source":
            self.source = create_source_markdown(self.name, self.path, self.filters)

    def convert_markdown(self, source: str, anchor: str) -> str:
        """Return converted markdown."""
        if self.kind in ["object", "source"]:  # noqa: SIM102
            if self.markdown and not is_module_cache_dirty(self.name):
                return self.markdown
        if self.kind == "markdown":
            self.source = source
        paths = source_paths if self.kind == "source" else object_paths

        self.markdown = convert_markdown(self.source, self.path, paths, anchor)
        return self.markdown


object_paths: dict[str, Path] = {}


def create_object_markdown(
    name: str,
    path: Path,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> str:
    """Create object page for an object."""
    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    filters_str = "|" + "|".join(filters) if filters else ""

    markdowns = []
    for child, depth in iter_objects_with_depth(obj, 2, member_only=True):
        if is_empty(child):
            continue
        if predicate and not predicate(child.fullname):
            continue
        object_paths.setdefault(child.fullname, path)

        heading = "#" * (depth + 1)
        markdown = f"{heading} ::: {child.fullname}{filters_str}\n"
        markdowns.append(markdown)

    return "\n".join(markdowns)


source_paths: dict[str, Path] = {}


def create_source_markdown(
    name: str,
    path: Path,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> str:
    """Create source page for a module."""
    if not (obj := get_object(name)) or not isinstance(obj, Module):
        return f"!!! failure\n\n    module {name!r} not found.\n"

    object_filters = []
    for child in iter_objects(obj, 2):
        if predicate and not predicate(child.fullname):
            continue
        if object_filter := get_object_filter_for_source(child, obj):
            object_filters.append(object_filter)
        source_paths.setdefault(child.fullname, path)

    filters_str = "|" + "|".join([*filters, "source", *object_filters])
    return f"# ::: {name}{filters_str}\n"


def convert_markdown(
    markdown: str,
    path: Path,
    paths: dict[str, Path],
    anchor: str,
) -> str:
    """Return converted markdown."""
    markdown = mkapi.markdown.sub(OBJECT_PATTERN, _replace_object, markdown)

    def replace_link(match: re.Match) -> str:
        return _replace_link(match, path.parent, paths, anchor)

    # replace_link = partial(_replace_link, directory=path.parent, anchor=anchor)
    return mkapi.markdown.sub(LINK_PATTERN, replace_link, markdown)


OBJECT_PATTERN = re.compile(r"^(?P<heading>#*) *?::: (?P<name>.+?)$", re.M)


def _replace_object(match: re.Match) -> str:
    heading, name = match.group("heading"), match.group("name")
    level = len(heading)
    name, filters = split_filters(name)

    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    return mkapi.renderers.render(obj, level, filters)


LINK_PATTERN = re.compile(r"(?<!`)\[([^[\]\s]+?)\]\[([^[\]\s]+?)\]")


def _replace_link(
    match: re.Match,
    directory: Path,
    paths: dict[str, Path],
    anchor: str = "source",
) -> str:
    name, fullname = match.groups()
    fullname, filters = split_filters(fullname)

    if fullname.startswith("__mkapi__.__source__."):
        name = f"[{anchor}]"
        paths = source_paths
        return _replace_link_from_paths(name, fullname[21:], directory, paths) or ""

    if "source" in filters:
        paths = source_paths
        # return _replace_link_from_paths(name, fullname, directory, paths) or name

    return _replace_link_from_paths(name, fullname, directory, paths) or match.group()


def _replace_link_from_paths(
    name: str,
    fullname: str,
    directory: Path,
    paths: dict[str, Path],
) -> str | None:
    fullname, from_mkapi = _resolve_fullname(fullname)

    if path := paths.get(fullname):
        uri = path.relative_to(directory, walk_up=True).as_posix()
        return f'[{name}]({uri}#{fullname} "{fullname}")'

    if from_mkapi:
        return f'<span class="mkapi-tooltip" title="{fullname}">{name}</span>'

    return None


def _resolve_fullname(fullname: str) -> tuple[str, bool]:
    if fullname.startswith("__mkapi__."):
        from_mkapi = True
        fullname = fullname[10:]
    else:
        from_mkapi = False

    fullname = resolve_with_attribute(fullname) or fullname
    return fullname, from_mkapi


SOURCE_LINK_PATTERN = re.compile(r"(<span[^<]+?)## __mkapi__\.(\S+?)(</span>)")


def convert_source(html: str, path: Path, anchor: str) -> str:
    """Convert HTML for source pages."""

    def replace(match: re.Match) -> str:
        open_tag, name, close_tag = match.groups()
        if object_path := object_paths.get(name):
            uri = object_path.relative_to(path, walk_up=True).as_posix()
            uri = uri[:-3]  # Remove `.md`
            uri = uri.replace("/README", "")  # Remove `/README`
            href = f"{uri}/#{name}"
            link = f'<a href="{href}">[{anchor}]</a>'
            link = f'<span id="{name}" class="mkapi-docs-link">{link}</span>'
        else:
            link = ""
        if open_tag.endswith(">"):
            return link
        return f"{open_tag}{close_tag}{link}"

    return SOURCE_LINK_PATTERN.sub(replace, html)
