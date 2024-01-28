"""Page class that works with other converter."""
from __future__ import annotations

import re
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from mkapi.globals import resolve_with_attribute
from mkapi.importlib import get_object
from mkapi.objects import is_empty, iter_objects_with_depth
from mkapi.renderers import render
from mkapi.utils import split_filters, update_filters

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


object_paths: dict[str, Path] = {}


def create_page(
    name: str,
    path: Path,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> None:
    """Create API page."""

    def _predicate(name: str) -> bool:
        if predicate and not predicate(name):
            return False
        object_paths.setdefault(name, path)
        return True

    names = [x.strip() for x in name.split(",")]

    with path.open("w") as file:
        for name in names:
            markdown = _create_page(name, filters, _predicate)
            file.write(markdown)
            if name != names[-1]:
                file.write("\n")


NAME_PATTERN = re.compile(r"^(.+?)(\.\*+)?$")


def _create_page(
    name: str,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> str:
    """Create markdown."""
    if m := NAME_PATTERN.match(name):
        name = m.group(1)
        maxdepth = int(len(m.group(2) or ".")) - 1
    else:
        maxdepth = 0
    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."
    markdowns = []
    filters_str = "|" + "|".join(filters) if filters else ""
    for obj_, depth in iter_objects_with_depth(obj, maxdepth):
        name = obj_.fullname
        if is_empty(obj_):
            continue
        if predicate and not predicate(name):
            continue
        heading = "#" * (depth + 1)
        markdown = f"{heading} ::: {name}{filters_str}\n"
        markdowns.append(markdown)
    return "\n".join(markdowns)


OBJECT_PATTERN = re.compile(r"^(#*) *?::: (.+?)$", re.MULTILINE)


def _split_markdown(source: str) -> Iterator[tuple[str, int, list[str]]]:
    """Yield tuples of (text, level, filters)."""
    cursor = 0
    for match in OBJECT_PATTERN.finditer(source):
        start, end = match.start(), match.end()
        if cursor < start and (markdown := source[cursor:start].strip()):
            yield markdown, -1, []
        cursor = end
        heading, name = match.groups()
        level = len(heading)
        name, filters = split_filters(name)
        yield name, level, filters
    if cursor < len(source) and (markdown := source[cursor:].strip()):
        yield markdown, -1, []


def convert_markdown(source: str, path: str, filters: list[str]) -> str:
    """Return converted markdown."""
    markdowns = []
    for name, level, filters_ in _split_markdown(source):
        if level == -1:
            markdowns.append(name)
        else:
            updated_filters = update_filters(filters, filters_)
            markdown = create_markdown(name, level, updated_filters)
            markdowns.append(markdown)
    markdown = "\n\n".join(markdowns)
    replace = partial(_replace_link, directory=Path(path).parent)
    return re.sub(LINK_PATTERN, replace, markdown)


def create_markdown(name: str, level: int, filters: list[str]) -> str:
    """Return a Markdown source."""
    if not (obj := get_object(name)):
        return f"!!! failure\n\n    {name!r} not found."

    heading = "#" * level + " " if level else ""
    prefix = obj.doc.type.markdown.split("..")
    self = obj.name.split(".")[-1].replace("_", "\\_")
    fullname = ".".join(prefix[:-1] + [self])
    id_ = obj.fullname.replace("_", "\\_")
    content = render(obj, filters)
    return f"{heading}{fullname} {{#{id_} .mkapi-object-heading}}\n\n{content}"


LINK_PATTERN = re.compile(r"\[(\S+?)\]\[(\S+?)\]")


def _replace_link(match: re.Match, directory: Path) -> str:
    asname, fullname = match.groups()
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
        return f'<span class="tooltip" title="{fullname}">{asname}</span>'
    return match.group()
