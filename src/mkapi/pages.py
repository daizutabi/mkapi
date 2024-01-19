"""Page class that works with other converter."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from mkapi import renderers
from mkapi.importlib import get_object, load_module
from mkapi.objects import Class, Function, Module, iter_objects, iter_texts, iter_types
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
        replace = partial(_replace_link, abs_src_path=self.abs_src_path)
        return re.sub(LINK_PATTERN, replace, markdown)

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


# TODO: `.*` and `.**` pattern for name.
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


# TODO: use doc.iter_types and doc.iter_texts instead of `iter_types` and `iter_texts`
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
    return renderers.render(obj, level, filters)


object_uris: dict[str, Path] = {}


def collect_objects(name: str | list[str], abs_path: Path) -> None:
    """Collect objects for link."""
    if isinstance(name, list):
        for name_ in name:
            collect_objects(name_, abs_path)
        return
    if not (module := load_module(name)):
        return
    for obj in iter_objects(module):
        object_uris.setdefault(obj.fullname, abs_path)


LINK_PATTERN = re.compile(r"\[(\S+?)\]\[(\S+?)\]")


def _replace_link(match: re.Match, abs_src_path: str) -> str:
    asname, fullname = match.groups()
    if fullname.startswith("__mkapi__."):
        from_mkapi = True
        fullname = fullname[10:]
    else:
        from_mkapi = False
    if uri := object_uris.get(fullname):
        uri = uri.relative_to(Path(abs_src_path).parent, walk_up=True).as_posix()
        return f"[{asname}]({uri}#{fullname})"
    return asname if from_mkapi else match.group()
