"""Page class that works with other converter."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# from mkapi.converter import convert_html, convert_object
from mkapi.link import resolve_link
from mkapi.utils import split_filters, update_filters

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


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
    abs_api_paths: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    headings: list[tuple[str, int]] = field(default_factory=list, init=False)

    def convert_markdown(self) -> str:  # noqa: D102
        return "\n\n".join(self._iter_markdown())

    def _resolve_link(self, markdown: str) -> str:
        return resolve_link(markdown, self.abs_src_path, self.abs_api_paths)

    def _iter_markdown(self) -> Iterator[str]:
        cursor = 0
        for match in MKAPI_PATTERN.finditer(self.source):
            start, end = match.start(), match.end()
            if cursor < start and (markdown := self.source[cursor:start].strip()):
                yield self._resolve_link(markdown)
            cursor = end
            heading, name = match.groups()
            level = len(heading)
            name, filters = split_filters(name)
            filters = update_filters(self.filters, filters)
            markdown = convert_object(name, level)  # TODO: callback for link.
            if level:
                self.headings.append((name, level))  # duplicated name?
            yield wrap_markdown(name, markdown, filters)
        if cursor < len(self.source) and (markdown := self.source[cursor:].strip()):
            yield self._resolve_link(markdown)
