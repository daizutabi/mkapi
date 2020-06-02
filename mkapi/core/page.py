import re
from dataclasses import dataclass, field
from typing import Iterator, List

from mkapi.core.node import Node, get_node
from mkapi.core.renderer import renderer

MKAPI_PATTERN = re.compile(r"^!\[mkapi\]\((.*?)\)$", re.MULTILINE)

HTML_PATTERN = re.compile(
    r"<!-- mkapi:(\d+):begin -->(.*?)<!-- mkapi:end -->", re.MULTILINE | re.DOTALL
)


@dataclass
class Page:
    source: str
    nodes: List[Node] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.markdown = "\n\n".join(self.split(self.source))

    def split(self, source) -> Iterator[str]:
        cursor = 0
        for index, match in enumerate(MKAPI_PATTERN.finditer(source)):
            start, end = match.start(), match.end()
            if cursor < start:
                markdown = source[cursor:start].strip()
                if markdown:
                    yield markdown
            name = match.group(1)
            if ":" in name:
                name, max_depth_str = name.split(":")
                max_depth = int(max_depth_str)
            else:
                max_depth = -1
            if name[0] == "#":
                headless = True
                name = name[1:]
            else:
                headless = False
            node = get_node(name, max_depth, headless)
            self.nodes.append(node)
            markdown = node.get_markdown()
            yield f"<!-- mkapi:{index}:begin -->\n\n{markdown}\n\n<!-- mkapi:end -->"
            cursor = end
        if cursor < len(source):
            markdown = source[cursor:].strip()
            if markdown:
                yield markdown

    def content(self, html):
        return re.sub(HTML_PATTERN, self.replace, html)

    def replace(self, match):
        node = self.nodes[int(match.group(1))]
        node.set_html(match.group(2))
        return renderer.render(node)
