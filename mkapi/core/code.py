import io
import re
from dataclasses import dataclass, field
from typing import List

import markdown

from mkapi.core.module import Module, get_module


@dataclass
class Code:
    module: Module
    markdown: str = field(default="", init=False)
    html: str = field(default="", init=False)
    level: int = field(default=1, init=False)

    def __post_init__(self):
        sourcefile = self.module.sourcefile
        with io.open(sourcefile, "r", encoding="utf-8-sig", errors="strict") as f:
            source = f.read()
        if not source:
            return

        nodes = []
        linenos = []
        for node in self.module.node.walk():
            if node.sourcefile == sourcefile:
                if node.lineno > 0 and node.lineno not in linenos:
                    nodes.append(node)
                    linenos.append(node.lineno)
        module_id = self.module.object.id
        i = 0
        lines = []
        for k, line in enumerate(source.split("\n")):
            if i < len(linenos) and k == linenos[i]:
                object_id = nodes[i].object.id
                lines.append(f"    # __mkapi__:{module_id}:{object_id}")
                i += 1
            lines.append("    " + line)
        source = "\n".join(lines)
        self.markdown = f"    :::python\n{source}\n"
        html = markdown.markdown(self.markdown, extensions=["codehilite"])
        self.html = replace(html)

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}({self.module.object.id!r})"

    def get_markdown(self, level: int = 1) -> str:
        """Returns a Markdown source for docstring of this object."""
        self.level = level
        return f"# {self.module.object.id}"

    def set_html(self, html: str):
        pass

    def get_html(self, filters: List[str] = None) -> str:
        """Renders and returns HTML."""
        from mkapi.core.renderer import renderer

        return renderer.render_code(self, filters)  # type:ignore


COMMENT_PATTERN = re.compile(r'\n<span class="c1"># __mkapi__:(.*?):(.*?)</span>')


def replace(html):
    def func(match):
        module, object = match.groups()
        link = f'<span id="{object}"></span>'
        link += f'<a class="mkapi-docs-link" title="{object}" '
        link += f'href="../../{module}#{object}">DOCS</a>'
        return link

    return COMMENT_PATTERN.sub(func, html)


def get_code(name: str) -> Code:
    module = get_module(name)
    return Code(module)
