"""This module provides a Page class that works with other converter."""
import re
from dataclasses import InitVar, dataclass, field
from typing import Iterator, List

from mkapi import utils
from mkapi.core.base import Base, Section
from mkapi.core.inherit import inherit_by_filters
from mkapi.core.linker import resolve_link
from mkapi.core.node import Node, get_node
from mkapi.core.regex import MKAPI_PATTERN, NODE_PATTERN, node_markdown
from mkapi.core.renderer import renderer
from mkapi.core import postprocess


@dataclass
class Page:
    """Page class works with [MkapiPlugin](mkapi.plugins.mkdocs.MkapiPlugin).

    Args:
        source (str): Markdown source.
        abs_src_path: Absolute source path of Markdown.
        abs_api_paths: A list of API paths.

    Attributes:
        markdown: Converted Markdown including API documentation.
        nodes: A list of Node instances.
    """

    source: InitVar[str]
    abs_src_path: str
    abs_api_paths: List[str] = field(default_factory=list, repr=False)
    markdown: str = field(init=False, repr=False)
    nodes: List[Node] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self, source):
        self.markdown = "\n\n".join(self.split(source))

    def resolve_link(self, markdown: str):
        return resolve_link(markdown, self.abs_src_path, self.abs_api_paths)

    def resolve_link_from_base(self, base: Base):
        if isinstance(base, Section) and base.name in ["Example", "Examples"]:
            return base.markdown
        return resolve_link(base.markdown, self.abs_src_path, self.abs_api_paths)

    def split(self, source: str) -> Iterator[str]:
        cursor = 0
        callback = self.resolve_link_from_base
        for index, match in enumerate(MKAPI_PATTERN.finditer(source)):
            start, end = match.start(), match.end()
            if cursor < start:
                markdown = source[cursor:start].strip()
                if markdown:
                    yield self.resolve_link(markdown)
            heading, name = match.groups()
            name, filters = utils.filter(name)
            node = get_node(name)
            inherit_by_filters(node, filters)
            postprocess.transform(node, filters)
            self.nodes.append(node)
            markdown = node.get_markdown(level=len(heading), callback=callback)
            yield node_markdown(index, markdown, filters)
            cursor = end
        if cursor < len(source):
            markdown = source[cursor:].strip()
            if markdown:
                yield self.resolve_link(markdown)

    def content(self, html: str) -> str:
        """Returns updated HTML to [MkapiPlugin](mkapi.plugins.mkdocs.MkapiPlugin).

        Args:
            html: Input HTML converted by MkDocs.
        """

        def replace(match):
            node = self.nodes[int(match.group(1))]
            filters = match.group(2).strip("|")
            node.set_html(match.group(3))
            return renderer.render(node, filters=filters)

        return re.sub(NODE_PATTERN, replace, html)
