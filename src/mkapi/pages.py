"""Page class that works with other converter."""
from __future__ import annotations

import datetime
import os.path
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

import mkapi.markdown
import mkapi.renderers
from mkapi.globals import resolve_with_attribute
from mkapi.importlib import get_object, load_module
from mkapi.objects import is_empty, is_member, iter_objects_with_depth
from mkapi.utils import split_filters

if TYPE_CHECKING:
    from mkapi.objects import Attribute, Class, Function, Module

PageKind = Enum("PageKind", ["OBJECT", "SOURCE", "MARKDOWN"])

object_paths: dict[str, dict[str, Path]] = {}


@dataclass
class Page:
    """Page class."""

    name: str
    path: Path
    kind: PageKind
    filters: list[str]
    markdown: str = ""

    def __post_init__(self) -> None:
        if not self.path.exists():
            if not self.path.parent.exists():
                self.path.parent.mkdir(parents=True)

            self.create_markdown()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!r})"

    def create_markdown(self) -> None:
        """Create markdown source."""
        if self.kind in [PageKind.OBJECT, PageKind.SOURCE]:
            with self.path.open("w") as file:
                file.write(f"{datetime.datetime.now()}")  # noqa: DTZ005

            self.markdown, names = create_markdown(self.name, self.filters)

            namespace = "source" if PageKind.SOURCE else "object"

            if namespace not in object_paths:
                object_paths[namespace] = {}

            for name in names:
                object_paths[namespace][name] = self.path

    def convert_markdown(self, markdown: str, anchors: dict[str, str]) -> str:
        """Return converted markdown."""
        if self.kind in [PageKind.OBJECT, PageKind.SOURCE]:
            markdown = self.markdown

        namespaces = ("object", "source") if PageKind.SOURCE else ("source", "object")

        return convert_markdown(markdown, self.path, namespaces, object_paths, anchors)

    def convert_html(self, html: str, anchors: dict[str, str]) -> str:
        """Return converted html."""

        namespace = "object" if PageKind.SOURCE else "source"
        paths = object_paths[namespace]
        anchor = anchors[namespace]

        return convert_html(html, self.path, paths, anchor)


Predicate: TypeAlias = Callable[[str], bool] | None


def create_markdown(
    name: str,
    filters: list[str],
    predicate: Predicate = None,
) -> tuple[str, list[str]]:
    """Create object page for an object."""
    if not (module := load_module(name)):
        return f"!!! failure\n\n    module {name!r} not found.\n", []

    filters_str = "|" + "|".join(filters) if filters else ""

    predicate_ = partial(_predicate, predicate=predicate)

    markdowns = []
    names = []

    for obj, depth in iter_objects_with_depth(module, 2, predicate_):
        names.append(obj.fullname.str)
        heading = "#" * (depth + 1)
        markdown = f"{heading} ::: {obj.fullname.str}{filters_str}\n"
        markdowns.append(markdown)

    return "\n".join(markdowns), names


def _predicate(
    obj: Module | Class | Function | Attribute,
    parent: Module | Class | Function | None,
    predicate: Callable[[str], bool] | None,
) -> bool:
    if not is_member(obj, parent):
        return False
    if is_empty(obj):
        return False
    if predicate and not predicate(obj.fullname.str):
        return False
    return True


OBJECT_PATTERN = re.compile(r"^(?P<heading>#*) *?::: (?P<name>.+?)$", re.M)
LINK_PATTERN = re.compile(r"(?<!`)\[([^[\]\s]+?)\]\[([^[\]\s]+?)\]")


def convert_markdown(
    markdown: str,
    path: Path,
    namespaces: tuple[str, str],
    paths: dict[str, dict[str, Path]],
    anchors: dict[str, str],
) -> str:
    """Return converted markdown."""
    render = partial(_render, namespace=namespaces[1])
    markdown = mkapi.markdown.sub(OBJECT_PATTERN, render, markdown)

    def replace_link(match: re.Match) -> str:
        return _replace_link(match, path.parent, namespaces[0], paths, anchors)

    return mkapi.markdown.sub(LINK_PATTERN, replace_link, markdown)


def _render(match: re.Match, namespace: str) -> str:
    heading, name = match.groups()
    level = len(heading)
    name, filters = split_filters(name)

    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    return mkapi.renderers.render(obj, level, namespace, filters)


OBJECT_LINK_PATTERN = re.compile(r"^__mkapi__\.__(.+)__\.(.+)$")


def _replace_link(
    match: re.Match,
    directory: Path,
    namespace: str,
    paths: dict[str, dict[str, Path]],
    anchors: dict[str, str],
) -> str:
    name, fullname = match.groups()
    fullname, filters = split_filters(fullname)

    asname = ""

    if m := OBJECT_LINK_PATTERN.match(fullname):
        namespace, fullname = m.groups()

        if namespace in anchors and namespace in paths:
            name = f"[{anchors[namespace]}]"
            paths_ = paths[namespace]
        else:
            return ""

    else:
        paths_ = paths[namespace]
        asname = match.group()

    # if "source" in filters:
    #     paths = source_paths

    return _replace_link_from_paths(name, fullname, directory, paths_) or asname


def _replace_link_from_paths(name: str, fullname: str, directory: Path, paths: dict[str, Path]) -> str | None:
    if fullname.startswith("__mkapi__."):
        from_mkapi = True
        fullname = fullname[10:]
    else:
        from_mkapi = False

    fullname = resolve_with_attribute(fullname) or fullname

    if path := paths.get(fullname):
        # Python 3.12
        # uri = path.relative_to(directory, walk_up=True).as_posix()
        uri = Path(os.path.relpath(path, directory)).as_posix()
        return f'[{name}]({uri}#{fullname} "{fullname}")'

    if from_mkapi:
        return f'<span class="mkapi-tooltip" title="{fullname}">{name}</span>'

    return None


SOURCE_LINK_PATTERN = re.compile(r"(<span[^<]+?)## __mkapi__\.(\S+?)(</span>)")
HEADING_PATTERN = re.compile(r"<h\d.+?mkapi-heading.+?</h\d>\n?")


def convert_html(html: str, path: Path, paths: dict[str, Path], anchor: str) -> str:
    """Convert HTML for source pages."""

    def replace(match: re.Match) -> str:
        open_tag, name, close_tag = match.groups()

        if object_path := paths.get(name):
            # Python 3.12
            # uri = object_path.relative_to(path, walk_up=True).as_posix()
            uri = Path(os.path.relpath(object_path, path)).as_posix()
            uri = uri[:-3]  # Remove `.md`
            uri = uri.replace("/README", "")  # Remove `/README`

            href = f"{uri}/#{name}"
            link = f'<a href="{href}">[{anchor}]</a>'
            link = f'<span class="mkapi-source-link" id="{name}">{link}</span>'
        else:
            link = ""

        if open_tag.endswith(">"):
            return link

        return f"{open_tag}{close_tag}{link}"

    html = SOURCE_LINK_PATTERN.sub(replace, html)
    return HEADING_PATTERN.sub("", html)
