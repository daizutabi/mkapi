"""Page class that works with other converter."""
from __future__ import annotations

import re
from functools import partial
from pathlib import Path
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

NAME_PATTERN = re.compile(r"^(?P<name>.+?)(?P<maxdepth>\.\*+)?$")


def _split_name_maxdepth(name: str) -> tuple[str, int]:
    if m := NAME_PATTERN.match(name):
        name = m.group("name")
        maxdepth = int(len(m.group("maxdepth") or ".")) - 1
    else:
        maxdepth = 0
    return name, maxdepth


def create_object_page(
    name: str,
    path: Path,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> None:
    """Create API page."""
    with path.open("w") as file:
        markdown = _create_object_page(name, path, filters, predicate)
        file.write(markdown)


object_paths: dict[str, Path] = {}


def _create_object_page(
    name: str,
    path: Path,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> str:
    """Create markdown."""
    name, maxdepth = _split_name_maxdepth(name)
    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    markdowns = []
    filters_str = "|" + "|".join(filters) if filters else ""
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


def create_source_page(
    name: str,
    path: Path,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> None:
    """Create source page."""
    with path.open("w") as file:
        markdown = _create_source_page(name, path, filters, predicate)
        file.write(markdown)


def _create_source_page(
    name: str,
    path: Path,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> str:
    name, maxdepth = _split_name_maxdepth(name)
    if not (obj := get_object(name)) or not isinstance(obj, Module):
        return f"!!! failure\n\n    module {name!r} not found.\n"

    object_filters = []
    for child in iter_objects(obj, maxdepth):
        if predicate and not predicate(child.fullname):
            continue
        # if isinstance(child, Module):
        #     obj_ = f"__mkapi__:{child.fullname}=0"
        # elif obj.name == child.module.name and child.node:
        #     obj_ = f"__mkapi__:{child.fullname}={child.node.lineno-1}"
        # else:
        #     continue
        # object_filters.append(obj_)
        if object_filter := get_object_filter_for_source(child, obj):
            object_filters.append(object_filter)
        source_paths.setdefault(child.fullname, path)

    filters_str = "|" + "|".join([*filters, "source", *object_filters])
    return f"# ::: {name}{filters_str}\n"


# def _split_markdown(source: str) -> Iterator[tuple[str, int, list[str]]]:
#     """Yield tuples of (text, level, filters)."""
#     for match in mkapi.markdown.finditer(OBJECT_PATTERN, source):
#         if isinstance(match, str):
#             yield match, -1, []
#         else:
#             heading, name = match.group("heading"), match.group("name")
#             level = len(heading)
#             name, filters = split_filters(name)
#             yield name, level, filters

# cursor = 0
# for match in OBJECT_PATTERN.finditer(source):
#     print(match)
#     start, end = match.start(), match.end()
#     if cursor < start and (markdown := source[cursor:start].strip()):
#         yield markdown, -1, []
#     cursor = end
#     heading, name = match.groups()
#     if name.startswith("__mkapi__."):
#         yield match.group().replace("__mkapi__.", ""), -1, []
#         continue
#     level = len(heading)
#     name, filters = split_filters(name)
#     yield name, level, filters
# if cursor < len(source) and (markdown := source[cursor:].strip()):
#     yield markdown, -1, []

OBJECT_PATTERN = re.compile(r"^(?P<heading>#*) *?::: (?P<name>.+?)$", re.M)


def convert_markdown(source: str, path: str, anchor: str, filters: list[str]) -> str:
    """Return converted markdown."""

    def replace_object(match: re.Match) -> str:
        heading, name = match.group("heading"), match.group("name")
        level = len(heading)
        name, filters_ = split_filters(name)
        updated_filters = update_filters(filters, filters_)
        return create_markdown(name, level, updated_filters)

    markdown = mkapi.markdown.sub(OBJECT_PATTERN, replace_object, source)

    # markdowns = []
    # for name, level, filters_ in _split_markdown(source):
    #     if level == -1:
    #         markdowns.append(name)
    #     else:
    #         updated_filters = update_filters(filters, filters_)
    #         markdown = create_markdown(name, level, updated_filters)
    #         markdowns.append(markdown)
    # markdown = "\n\n".join(markdowns)
    # return re.sub(LINK_PATTERN, replace_link, markdown)
    replace_link = partial(_replace_link, directory=Path(path).parent, anchor=anchor)
    return mkapi.markdown.sub(LINK_PATTERN, replace_link, markdown)


def create_markdown(name: str, level: int, filters: list[str]) -> str:
    """Return a Markdown source."""
    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    return mkapi.renderers.render(obj, level, filters)


LINK_PATTERN = re.compile(r"(?<!`)\[([^[\]\s]+?)\]\[([^[\]\s]+?)\]")


def _replace_link(match: re.Match, directory: Path, anchor: str = "source") -> str:
    asname, fullname = match.groups()
    fullname, filters = split_filters(fullname)
    if fullname.startswith("__mkapi__.__source__."):
        fullname = fullname[21:]
        if source_path := source_paths.get(fullname):
            uri = source_path.relative_to(directory, walk_up=True).as_posix()
            return f'[[{anchor}]]({uri}#{fullname} "{fullname}")'
        return ""

    if "source" in filters:
        if source_path := source_paths.get(fullname):
            uri = source_path.relative_to(directory, walk_up=True).as_posix()
            return f'[{asname}]({uri}#{fullname} "{fullname}")'
        return asname

    if fullname.startswith("__mkapi__."):
        from_mkapi = True
        fullname = fullname[10:]
    else:
        from_mkapi = False
    if fullname_ := resolve_with_attribute(fullname):
        fullname = fullname_
    if object_path := object_paths.get(fullname):
        uri = object_path.relative_to(directory, walk_up=True).as_posix()
        return f'[{asname}]({uri}#{fullname} "{fullname}")'
    if from_mkapi:
        return f'<span class="mkapi-tooltip" title="{fullname}">{asname}</span>'
    return match.group()


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
