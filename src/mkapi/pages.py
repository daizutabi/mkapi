"""Page class that works with other converter."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from mkapi import renderers
from mkapi.importlib import get_object, iter_texts, iter_types
from mkapi.objects import Class, Function, Module
from mkapi.utils import split_filters, update_filters

# from mkapi.converter import convert_html, convert_object

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.items import Text, Type


@dataclass(repr=False)
class Page:
    """Page class works with [MkAPIPlugin][mkapi.plugins.MkAPIPlugin].

    Args:
        source: Markdown source.
        abs_src_path: Absolute source path of Markdown.
        abs_api_paths: A list of API paths.

    Attributes:
        markdown: Converted Markdown including API documentation.
        nodes: A list of Node instances.
    """

    source: str
    abs_src_path: str
    abs_api_paths: list[str]
    filters: list[list[str]] = field(default_factory=list)
    objects: list[Module | Class | Function] = field(default_factory=list, init=False)
    levels: list[int] = field(default_factory=list, init=False)

    def convert_markdown(self) -> str:  # noqa: D102
        index, markdowns = 0, []
        for name, level, filters in _iter_markdown(self.source):
            if level == -1:
                markdowns.append(name)
            else:
                markdown = self._callback_markdown(name, level, filters)
                markdowns.append(_object_markdown(markdown, index))
                index += 1
        markdown = "\n\n".join(markdowns)
        return resolve_link(markdown, self.abs_src_path, self.abs_api_paths)

    def _callback_markdown(self, name: str, level: int, filters: list[str]) -> str:
        obj = get_object(name)
        if not isinstance(obj, Module | Class | Function):
            raise NotImplementedError
        self.objects.append(obj)
        self.levels.append(level)
        self.filters.append(filters)
        return get_markdown(obj)

    def convert_html(self, html: str) -> str:  # noqa: D102
        def replace(match: re.Match) -> str:
            index, html = match.groups()
            return self._callback_html(int(index), html)

        return re.sub(NODE_PATTERN, replace, html)

    def _callback_html(self, index: int, html: str) -> str:
        obj = self.objects[index]
        level = self.levels[index]
        filters = self.filters[index]
        return convert_html(obj, html, level, filters)


OBJECT_PATTERN = re.compile(r"^(#*) *?::: (.+?)$", re.MULTILINE)


def _iter_markdown(source: str) -> Iterator[tuple[str, int, list[str]]]:
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


def _iter_type_text(obj: Module | Class | Function) -> Iterator[Type | Text]:
    for type_ in iter_types(obj):
        if type_.markdown:
            yield type_
    for text in iter_texts(obj):
        if text.markdown:
            yield text


def get_markdown(obj: Module | Class | Function) -> str:
    """Return a Markdown source."""
    markdowns = []
    for type_text in _iter_type_text(obj):
        markdowns.append(type_text.markdown)  # noqa: PERF401
    return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)


def convert_html(
    obj: Module | Class | Function,
    html: str,
    level: int,
    filters: list[str],
) -> str:
    """Convert HTML input."""
    htmls = html.split("<!-- mkapi:sep -->")
    for type_text, html in zip(_iter_type_text(obj), htmls, strict=True):
        type_text.html = html.strip()
    # return renderers.render(obj, level, filters)
    return html


LINK_PATTERN = re.compile(r"\[(\S+?)\]\[(\S+?)\]")


def resolve_link(markdown: str, abs_src_path: str, abs_api_paths: list[str]) -> str:
    """Reutrn resolved link.

    Args:
        markdown: Markdown source.
        abs_src_path: Absolute source path of Markdown.
        abs_api_paths: List of API paths.

    Examples:
        >>> abs_src_path = '/src/examples/example.md'
        >>> abs_api_paths = ['/api/a','/api/b', '/api/b.c']
        >>> resolve_link('[abc][b.c.d]', abs_src_path, abs_api_paths)
        '[abc](../../api/b.c#b.c.d)'
        >>> resolve_link('[abc][__mkapi__.b.c.d]', abs_src_path, abs_api_paths)
        '[abc](../../api/b.c#b.c.d)'
        >>> resolve_link('list[[abc][__mkapi__.b.c.d]]', abs_src_path, abs_api_paths)
        'list[[abc](../../api/b.c#b.c.d)]'
    """

    def replace(match: re.Match) -> str:
        name, href = match.groups()
        if href.startswith("!__mkapi__."):  # Just for MkAPI documentation.
            href = href[11:]
            return f"[{name}]({href})"
        from_mkapi = False
        if href.startswith("__mkapi__."):
            href = href[10:]
            from_mkapi = True

        if href := _resolve_href(href, abs_src_path, abs_api_paths):
            # print(f"[{name}]({href})")
            return f"[{name}]({href})"
        return name if from_mkapi else match.group()

    return re.sub(LINK_PATTERN, replace, markdown)


def _resolve_href(name: str, abs_src_path: str, abs_api_paths: list[str]) -> str:
    if not name:
        return ""
    abs_api_path = _match_last(name, abs_api_paths)
    if not abs_api_path:
        return ""
    relpath = os.path.relpath(abs_api_path, Path(abs_src_path).parent)
    relpath = relpath.replace("\\", "/")
    return f"{relpath}#{name}"


# TODO: match longest.
def _match_last(name: str, abs_api_paths: list[str]) -> str:
    match = ""
    for abs_api_path in abs_api_paths:
        _, path = os.path.split(abs_api_path)
        if name.startswith(path[:-3]):
            match = abs_api_path
    return match
