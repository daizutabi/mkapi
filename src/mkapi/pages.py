"""Page class that works with other converter."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# from mkapi.converter import convert_html, convert_object
from mkapi.link import resolve_link
from mkapi.nodes import get_node
from mkapi.utils import split_filters, update_filters

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from mkapi.nodes import Node


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


def convert_markdown(
    source: str,
    callback: Callable[[str, int, list[str]], str],
) -> str:
    """Return a converted markdown."""
    index, texts = 0, []
    for name, level, filters in _iter_markdown(source):
        if level == -1:
            texts.append(name)
        else:
            text = callback(name, level, filters)
            texts.append(f"<!-- mkapi:begin[{index}] -->\n{text}\n<!-- mkapi:end -->")
            index += 1
    return "\n\n".join(texts)


pattern = r"<!-- mkapi:begin\[(\d+)\] -->\n(.*?)\n<!-- mkapi:end -->"
NODE_PATTERN = re.compile(pattern, re.MULTILINE | re.DOTALL)


def convert_html(source: str, callback: Callable[[int, str], str]) -> str:
    """Return modified HTML."""

    def replace(match: re.Match) -> str:
        index, html = match.groups()
        return callback(int(index), html)

    return re.sub(NODE_PATTERN, replace, source)


@dataclass(repr=False)
class Page:
    """Page class works with [MkAPIPlugin](mkapi.plugins.mkdocs.MkAPIPlugin).

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
    nodes: list[Node] = field(default_factory=list)
    levels: list[int] = field(default_factory=list)
    filters: list[list[str]] = field(default_factory=list)

    def _callback_markdown(self, name: str, level: int, filters: list[str]) -> str:
        node = get_node(name)
        self.nodes.append(node)
        self.levels.append(level)
        self.filters.append(filters)
        return node.get_markdown(level, filters)

    def convert_markdown(self) -> str:  # noqa: D102
        markdown = convert_markdown(self.source, self._callback_markdown)
        return resolve_link(markdown, self.abs_src_path, self.abs_api_paths)

    def _callback_html(self, index: int, html: str) -> str:
        node = self.nodes[index]
        level = self.levels[index]
        filters = self.filters[index]
        return node.convert_html(html, level, filters)

    def convert_html(self, html: str) -> str:  # noqa: D102
        return convert_html(html, self._callback_html)
