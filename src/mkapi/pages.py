"""Page class that works with other converter."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from mkapi import renderers
from mkapi.importlib import get_object
from mkapi.items import Type
from mkapi.objects import Attribute, Class, Function, Module
from mkapi.utils import delete_ptags, split_filters, update_filters

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

type Object = Module | Class | Function | Attribute


@dataclass(repr=False)
class Page:
    """Page class works with [MkAPIPlugin][mkapi.plugins.MkAPIPlugin].

    Args:
        source: Markdown source.
        path: Absolute source path of Markdown.

    Attributes:
        markdown: Converted Markdown including API documentation.
        nodes: A list of Node instances.
    """

    source: str
    path: str
    filters: list[list[str]] = field(default_factory=list)
    objects: list[Object] = field(default_factory=list, init=False)
    levels: list[int] = field(default_factory=list, init=False)

    def convert_markdown(self) -> str:  # noqa: D102
        index, markdowns = 0, []
        for name, level, filters in split_markdown(self.source):
            if level == -1:
                markdowns.append(name)
            else:
                markdown = self._callback_markdown(name, level, filters)
                markdowns.append(_object_markdown(markdown, index))
                index += 1
        markdown = "\n\n".join(markdowns)
        replace = partial(_replace_link, directory=Path(self.path).parent)
        return re.sub(LINK_PATTERN, replace, markdown)

    def _callback_markdown(self, name: str, level: int, filters: list[str]) -> str:
        obj = get_object(name)
        if not isinstance(obj, Module | Class | Function | Attribute):
            raise NotImplementedError
        self.objects.append(obj)
        self.levels.append(level)
        self.filters.append(filters)
        return get_markdown(obj, level)

    def convert_html(
        self,
        html: str,
        callback: Callable[..., str] | None = None,
    ) -> str:
        """Convert HTML."""
        return html
        if not callback:
            callback = renderers.render

        def replace(match: re.Match) -> str:
            index, html = match.groups()
            return self._callback_html(html, int(index), callback)

        return re.sub(NODE_PATTERN, replace, html)

    def _callback_html(
        self,
        html: str,
        index: int,
        callback: Callable[..., str],
    ) -> str:
        obj = self.objects[index]
        level = self.levels[index]
        filters = self.filters[index]
        set_html(obj, html, level)
        return callback(obj, level, filters)


object_paths: dict[str, Path] = {}


def create_page(
    name: str,
    path: Path,
    level: int,
    filters: list[str],
    predicate: Callable[[str], bool] | None = None,
) -> None:
    """Create API page."""

    def _predicate(obj: Object) -> bool:
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


def split_markdown(source: str) -> Iterator[tuple[str, int, list[str]]]:
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


def _object_markdown(markdown: str, index: int) -> str:
    return f"<!-- mkapi:begin[{index}] -->\n\n{markdown}\n\n<!-- mkapi:end -->"


pattern = r"<!-- mkapi:begin\[(\d+)\] -->(.*?)<!-- mkapi:end -->"
NODE_PATTERN = re.compile(pattern, re.MULTILINE | re.DOTALL)


def get_markdown(obj: Object, level: int) -> str:
    """Return a Markdown source."""
    if level:
        fullname = obj.fullname.replace("_", "\\_")
        markdowns = ["#" * level + f" {fullname} {{#{fullname}}}"]
    else:
        markdowns = []
    for element in obj.doc:
        markdowns.append(element.markdown)
    return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)


def set_html(obj: Object, html: str, level: int) -> None:
    """Set HTML input."""
    htmls = html.split("<!-- mkapi:sep -->")
    if level:
        htmls = htmls[1:]
    for element, html in zip(obj.doc, htmls, strict=True):
        element.html = html.strip()
        if isinstance(element, Type):
            element.html = delete_ptags(element.html)


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
