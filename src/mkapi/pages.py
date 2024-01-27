"""Page class that works with other converter."""
from __future__ import annotations

import re
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from mkapi import renderers
from mkapi.importlib import get_object
from mkapi.utils import split_filters, update_filters

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from mkapi.objects import Attribute, Class, Function, Module


object_paths: dict[str, Path] = {}


def create_page(
    name: str,
    path: Path,
    level: int,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> None:
    """Create API page."""

    def _predicate(obj: Module | Class | Function | Attribute) -> bool:
        if predicate and not predicate(obj.fullname):
            return False
        object_paths.setdefault(obj.fullname, path)
        return True

    names = [x.strip() for x in name.split(",")]

    with path.open("w") as file:
        for name in names:
            markdown = renderers.render_markdown(name, level, filters, _predicate)
            file.write(markdown)
            if name != names[-1]:
                file.write("\n")


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
            markdown = get_markdown(name, level, updated_filters)
            markdowns.append(markdown)
    markdown = "\n\n".join(markdowns)
    replace = partial(_replace_link, directory=Path(path).parent)
    return re.sub(LINK_PATTERN, replace, markdown)


def get_markdown(name: str, level: int, filters: list[str]) -> str:
    """Return a Markdown source."""
    if not (obj := get_object(name)):
        return f"{name} not found."
    if level:
        fullname = obj.fullname.replace("_", "\\_")
        markdowns = ["#" * level + f" {fullname} {{#{fullname}}}"]
    else:
        markdowns = []
    for element in obj.doc:
        markdowns.append(element.markdown)
    return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)


LINK_PATTERN = re.compile(r"\[(\S+?)\]\[(\S+?)\]")


def _replace_link(match: re.Match, directory: Path) -> str:
    asname, fullname = match.groups()
    if fullname.startswith("__mkapi__."):
        from_mkapi = True
        fullname = fullname[10:]
    else:
        from_mkapi = False
    if object_path := object_paths.get(fullname):
        uri = object_path.relative_to(directory, walk_up=True).as_posix()
        return f"[{asname}]({uri}#{fullname})"
    return asname if from_mkapi else match.group()
