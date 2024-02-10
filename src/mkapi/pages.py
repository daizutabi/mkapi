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
from mkapi.utils import split_filters, update_filters

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
    markdown: str = field(init=False)

    def __post_init__(self) -> None:
        if not self.path.exists():
            if not self.path.parent.exists():
                self.path.parent.mkdir(parents=True)
            with self.path.open("w") as file:
                file.write("")

        if self.kind == "object":
            filters = [*self.filters, "sourcelink"]
            self.markdown = create_object_markdown(self.name, self.path, filters)
        elif self.kind == "source":
            self.markdown = create_source_markdown(self.name, self.path, self.filters)

    def convert_markdown(self, markdown: str, anchor: str) -> str:
        """Return converted markdown."""
        filters = self.filters
        if self.kind in ["object", "source"]:
            markdown = self.markdown

        return convert_markdown(markdown, self.path, anchor, filters)

        return '## titl\n xxx <h3 id="xx">section</h3>'


NAME_PATTERN = re.compile(r"^(?P<name>.+?)(?P<maxdepth>\.\*+)?$")


def _split_name_maxdepth(name: str) -> tuple[str, int]:
    if m := NAME_PATTERN.match(name):
        name = m.group("name")
        maxdepth = int(len(m.group("maxdepth") or ".")) - 1
    else:
        maxdepth = 0
    return name, maxdepth


object_paths: dict[str, Path] = {}


def create_object_markdown(
    name: str,
    path: Path,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> str:
    """Create object page for an object."""
    # name, maxdepth = _split_name_maxdepth(name)
    maxdepth = 2

    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    filters_str = "|" + "|".join(filters) if filters else ""

    markdowns = []
    for child, depth in iter_objects_with_depth(obj, maxdepth, member_only=True):
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
    # name, maxdepth = _split_name_maxdepth(name)
    maxdepth = 2

    if not (obj := get_object(name)) or not isinstance(obj, Module):
        return f"!!! failure\n\n    module {name!r} not found.\n"

    object_filters = []
    for child in iter_objects(obj, maxdepth):
        if predicate and not predicate(child.fullname):
            continue
        if object_filter := get_object_filter_for_source(child, obj):
            object_filters.append(object_filter)
        source_paths.setdefault(child.fullname, path)

    filters_str = "|" + "|".join([*filters, "source", *object_filters])
    return f"# ::: {name}{filters_str}\n"


def convert_markdown(markdown: str, path: Path, anchor: str, filters: list[str]) -> str:
    """Return converted markdown."""
    replace_object = partial(_replace_object, filters=filters)
    markdown = mkapi.markdown.sub(OBJECT_PATTERN, replace_object, markdown)

    replace_link = partial(_replace_link, directory=path.parent, anchor=anchor)
    return mkapi.markdown.sub(LINK_PATTERN, replace_link, markdown)


OBJECT_PATTERN = re.compile(r"^(?P<heading>#*) *?::: (?P<name>.+?)$", re.M)


def _replace_object(match: re.Match, filters: list[str]) -> str:
    heading, name = match.group("heading"), match.group("name")
    level = len(heading)
    name, filters_ = split_filters(name)

    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    updated_filters = update_filters(filters, filters_)

    return mkapi.renderers.render(obj, level, updated_filters)


LINK_PATTERN = re.compile(r"(?<!`)\[([^[\]\s]+?)\]\[([^[\]\s]+?)\]")


def _replace_link(match: re.Match, directory: Path, anchor: str = "source") -> str:
    asname, fullname = match.groups()
    fullname, filters = split_filters(fullname)

    if fullname.startswith("__mkapi__.__source__."):
        name = f"[{anchor}]"
        return _replace_link_from_source(name, fullname[21:], directory)

    if "source" in filters:
        return _replace_link_from_source(asname, fullname, directory) or asname

    return _replace_link_from_object(asname, fullname, directory) or match.group()


def _replace_link_from_object(name: str, fullname: str, directory: Path) -> str:
    if fullname.startswith("__mkapi__."):
        from_mkapi = True
        fullname = fullname[10:]
    else:
        from_mkapi = False

    if fullname_ := resolve_with_attribute(fullname):
        fullname = fullname_

    if object_path := object_paths.get(fullname):
        uri = object_path.relative_to(directory, walk_up=True).as_posix()
        return f'[{name}]({uri}#{fullname} "{fullname}")'

    if from_mkapi:
        return f'<span class="mkapi-tooltip" title="{fullname}">{name}</span>'

    return ""


def _replace_link_from_source(name: str, fullname: str, directory: Path) -> str:
    if source_path := source_paths.get(fullname):
        uri = source_path.relative_to(directory, walk_up=True).as_posix()
        return f'[{name}]({uri}#{fullname} "{fullname}")'

    return ""


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
