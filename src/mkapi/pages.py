"""Page class that works with other converter."""
from __future__ import annotations

import datetime
import os.path
import re
from dataclasses import dataclass
from enum import Enum
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import mkapi.markdown
import mkapi.renderers
from mkapi.globals import resolve_with_attribute
from mkapi.importlib import get_object, load_module
from mkapi.objects import is_empty, is_member, iter_objects_with_depth
from mkapi.renderers import get_object_filter_for_source
from mkapi.utils import split_filters

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkapi.objects import Attribute, Class, Function, Module

PageKind = Enum("PageKind", ["OBJECT", "SOURCE", "MARKDOWN"])


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

            self.markdown = create_markdown(
                self.name,
                self.path,
                self.kind,
                self.filters,
            )

    def convert_markdown(self, markdown: str, anchor: str) -> str:
        """Return converted markdown."""
        if self.kind in [PageKind.OBJECT, PageKind.SOURCE]:
            markdown = self.markdown

        return convert_markdown(
            markdown,
            self.path,
            self.kind,
            anchor,
        )


object_paths: dict[str, Path] = {}
source_paths: dict[str, Path] = {}


def create_markdown(
    name: str,
    path: Path,
    kind: PageKind,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> str:
    """Create object page for an object."""
    if not (module := load_module(name)):
        return f"!!! failure\n\n    module {name!r} not found.\n"

    filters_str = "|" + "|".join(filters) if filters else ""
    object_filter = ""

    paths = source_paths if kind is PageKind.SOURCE else object_paths

    predicate_ = partial(_predicate, predicate=predicate)

    markdowns = []
    for obj, depth in iter_objects_with_depth(module, 2, predicate_):
        paths[obj.fullname.str] = path

        if kind is PageKind.SOURCE:
            object_filter = get_object_filter_for_source(obj, module)
            object_filter = f"|{object_filter}" if object_filter else ""

        heading = "#" * (depth + 1)
        markdown = f"{heading} ::: {obj.fullname.str}{filters_str}{object_filter}\n"
        markdowns.append(markdown)

    return "\n".join(markdowns)


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


def convert_markdown(
    markdown: str,
    path: Path,
    kind: PageKind,
    anchor: str,
) -> str:
    """Return converted markdown."""
    if kind is PageKind.SOURCE:
        markdown = _replace_source(markdown)
    else:
        markdown = mkapi.markdown.sub(OBJECT_PATTERN, _replace_object, markdown)

    paths = source_paths if kind is PageKind.SOURCE else object_paths

    def replace_link(match: re.Match) -> str:
        return _replace_link(match, path.parent, paths, anchor)

    return mkapi.markdown.sub(LINK_PATTERN, replace_link, markdown)


OBJECT_PATTERN = re.compile(r"^(?P<heading>#*) *?::: (?P<name>.+?)$", re.M)


def _get_level_name_filters(match: re.Match) -> tuple[str, int, list[str]]:
    heading, name = match.groups()
    level = len(heading)
    name, filters = split_filters(name)
    return name, level, filters


def _replace_object(match: re.Match) -> str:
    name, level, filters = _get_level_name_filters(match)

    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    return mkapi.renderers.render(obj, level, filters, is_source=False)


def _replace_source(markdown: str) -> str:
    module = None
    filters = []
    headings = []

    for match in re.finditer(OBJECT_PATTERN, markdown):
        name, level, object_filter = _get_level_name_filters(match)
        if level == 1 and not (module := load_module(name)):
            break

        # Move to renderer.py
        if level >= 2:  # noqa: PLR2004
            # 'markdown="1"' for toc.
            attr = f'class="mkapi-dummy-heading" id="{name}" markdown="1"'
            name_ = name.replace("_", "\\_")
            heading = f"<h{level} {attr}>{name_}</h{level}>"
            headings.append(heading)
            filters.extend(object_filter)

    if not module:
        return "!!! failure\n\n    module not found."

    source = mkapi.renderers.render(module, 1, filters, is_source=True)
    return "\n".join([source, *headings])


LINK_PATTERN = re.compile(r"(?<!`)\[([^[\]\s]+?)\]\[([^[\]\s]+?)\]")


def _replace_link(
    match: re.Match,
    directory: Path,
    paths: dict[str, Path],
    anchor: str,
) -> str:
    name, fullname = match.groups()
    fullname, filters = split_filters(fullname)

    if fullname.startswith("__mkapi__.__source__."):
        name = f"[{anchor}]"
        paths = source_paths
        return _replace_link_from_paths(name, fullname[21:], directory, paths) or ""

    if fullname.startswith("__mkapi__.__object__."):
        name = f"[{anchor}]"
        paths = object_paths
        return _replace_link_from_paths(name, fullname[21:], directory, paths) or ""

    if "source" in filters:
        paths = source_paths

    return _replace_link_from_paths(name, fullname, directory, paths) or match.group()


def _replace_link_from_paths(
    name: str,
    fullname: str,
    directory: Path,
    paths: dict[str, Path],
) -> str | None:
    fullname, from_mkapi = _resolve_fullname(fullname)

    if path := paths.get(fullname):
        # Python 3.12
        # uri = path.relative_to(directory, walk_up=True).as_posix()
        uri = Path(os.path.relpath(path, directory)).as_posix()
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
HEADING_PATTERN = re.compile(r"<h\d.+?mkapi-dummy-heading.+?</h\d>\n?")


def convert_source(html: str, path: Path, anchor: str) -> str:
    """Convert HTML for source pages."""

    def replace(match: re.Match) -> str:
        open_tag, name, close_tag = match.groups()

        if object_path := object_paths.get(name):
            # Python 3.12
            # uri = object_path.relative_to(path, walk_up=True).as_posix()
            uri = Path(os.path.relpath(object_path, path)).as_posix()
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

    html = SOURCE_LINK_PATTERN.sub(replace, html)
    return HEADING_PATTERN.sub("", html)
