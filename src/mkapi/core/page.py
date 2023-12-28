"""Page class that works with other converter."""
import re
from collections.abc import Iterator
from dataclasses import InitVar, dataclass, field

from mkapi.core import postprocess
from mkapi.core.base import Base, Section
from mkapi.core.code import Code, get_code
from mkapi.core.filter import split_filters, update_filters
from mkapi.core.inherit import inherit
from mkapi.core.link import resolve_link
from mkapi.core.node import Node, get_node

MKAPI_PATTERN = re.compile(r"^(#*) *?!\[mkapi\]\((.+?)\)$", re.MULTILINE)
pattern = r"<!-- mkapi:begin:(\d+):\[(.*?)\] -->(.*?)<!-- mkapi:end -->"
NODE_PATTERN = re.compile(pattern, re.MULTILINE | re.DOTALL)


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
    abs_api_paths: list[str] = field(default_factory=list, repr=False)
    filters: list[str] = field(default_factory=list, repr=False)
    markdown: str = field(init=False, repr=False)
    nodes: list[Node | Code] = field(default_factory=list, init=False, repr=False)
    headings: list[tuple[int, str]] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    def __post_init__(self, source: str) -> None:
        self.markdown = "\n\n".join(self.split(source))

    def resolve_link(self, markdown: str) -> str:  # noqa: D102
        return resolve_link(markdown, self.abs_src_path, self.abs_api_paths)

    def resolve_link_from_base(self, base: Base) -> str:  # noqa: D102
        if isinstance(base, Section) and base.name in ["Example", "Examples"]:
            return base.markdown
        return resolve_link(base.markdown, self.abs_src_path, self.abs_api_paths)

    def split(self, source: str) -> Iterator[str]:  # noqa: D102
        callback = self.resolve_link_from_base
        cursor = index = 0
        for match in MKAPI_PATTERN.finditer(source):
            start, end = match.start(), match.end()
            if cursor < start:
                markdown = source[cursor:start].strip()
                if markdown:
                    yield self.resolve_link(markdown)
            cursor = end
            heading, name = match.groups()
            level = len(heading)
            name, filters = split_filters(name)
            if not name:
                self.filters = filters
                continue
            filters = update_filters(self.filters, filters)
            if "code" in filters:
                code = get_code(name)
                self.nodes.append(code)
                markdown = code.get_markdown(level)
            else:
                node = get_node(name)
                inherit(node)
                postprocess.transform(node, filters)
                self.nodes.append(node)
                markdown = node.get_markdown(level, callback=callback)
                if level:
                    self.headings.append((level, node.object.id))
            yield node_markdown(index, markdown, filters)
            index += 1
        if cursor < len(source):
            markdown = source[cursor:].strip()
            if markdown:
                yield self.resolve_link(markdown)

    def content(self, html: str) -> str:
        """Return updated HTML to [MkapiPlugin](mkapi.plugins.mkdocs.MkapiPlugin).

        Args:
            html: Input HTML converted by MkDocs.
        """

        def replace(match: re.Match) -> str:
            node = self.nodes[int(match.group(1))]
            filters = match.group(2).split("|")
            node.set_html(match.group(3))
            return node.get_html(filters)

        return re.sub(NODE_PATTERN, replace, html)


def node_markdown(index: int, markdown: str, filters: list[str] | None = None) -> str:
    """Return Markdown text for node."""
    fs = "|".join(filters) if filters else ""
    return f"<!-- mkapi:begin:{index}:[{fs}] -->\n\n{markdown}\n\n<!-- mkapi:end -->"
