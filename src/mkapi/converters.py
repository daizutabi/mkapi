"""Converter."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast

# from mkapi.converter import convert_html, convert_object
from mkapi.link import resolve_link
from mkapi.objects import load_module
from mkapi.utils import split_filters, update_filters

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from mkapi.objects import Module


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


def convert_module(name: str, filters: list[str]) -> str:
    """Convert the [Module] instance to markdown text."""
    if module := load_module(name):
        #     return renderer.render_module(module)
        return f"{module}: {id(module)}"
    return f"{name} not found"


def convert_object(name: str, level: int) -> str:
    return "# ac"


def convert_html(name: str, html: str, filters: list[str]) -> str:
    return f"xxxx  {html}"
