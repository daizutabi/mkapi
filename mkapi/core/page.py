import re
from dataclasses import dataclass, field
from typing import Iterator, List

from mkapi.core.inherit import inherit
from mkapi.core.linker import resolve_link
from mkapi.core.node import Node, get_node
from mkapi.core.regex import MKAPI_PATTERN, NODE_PATTERN, node_markdown
from mkapi.core.renderer import renderer
from mkapi import utils


@dataclass
class Page:
    source: str
    abs_src_path: str
    abs_api_paths: List[str] = field(default_factory=list)
    markdown: str = field(init=False)
    nodes: List[Node] = field(default_factory=list, init=False)

    def __post_init__(self):
        markdown = "\n\n".join(self.split(self.source))
        self.markdown = resolve_link(markdown, self.abs_src_path, self.abs_api_paths)

    def split(self, source) -> Iterator[str]:
        cursor = 0
        for index, match in enumerate(MKAPI_PATTERN.finditer(source)):
            start, end = match.start(), match.end()
            if cursor < start:
                markdown = source[cursor:start].strip()
                if markdown:
                    yield markdown
            heading, name = match.groups()
            name, filters = utils.filter(name)
            node = get_node(name, cache='nocache' not in filters)
            if node.object.kind in ["class", "dataclass"]:
                if "inherit" in filters:
                    inherit(node)
                elif "strict" in filters:
                    inherit(node, strict=True)
            self.nodes.append(node)
            markdown = node.get_markdown(level=len(heading))
            yield node_markdown(index, markdown, 'upper' in filters)
            cursor = end
        if cursor < len(source):
            markdown = source[cursor:].strip()
            if markdown:
                yield markdown

    def content(self, html):
        def replace(match):
            node = self.nodes[int(match.group(1))]
            node.set_html(match.group(3))
            renderer.upper = match.group(2) == "True"
            return renderer.render(node)

        return re.sub(NODE_PATTERN, replace, html)
