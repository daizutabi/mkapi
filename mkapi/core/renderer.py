import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.core.docstring import Docstring
from mkapi.core.node import Node


@dataclass
class Renderer:
    templates: Dict[str, Template] = field(default_factory=dict, init=False)

    def __post_init__(self):
        path = os.path.join(os.path.dirname(mkapi.__file__), "templates")
        loader = FileSystemLoader(path)
        env = Environment(loader=loader, autoescape=select_autoescape(["jinja2"]))
        for name in os.listdir(path):
            template = env.get_template(name)
            name = os.path.splitext(name)[0]
            self.templates[name] = template

    def render_node(
        self, node: Node, docstring: str, members: List[str], parent: Optional[Node]
    ) -> str:
        template = self.templates["node"]
        return template.render(node=node, members=members, parent=parent)

    def render_docstring(self, docstring: Docstring) -> str:
        template = self.templates["docstring"]
        return template.render(docstring=docstring)

    def render(self, node: Node, parent: Optional[Node] = None) -> str:
        docstring = self.render_docstring(node.docstring)
        members = []
        if node.members:
            members = [self.render(member, node) for member in node.members]
        return self.render_node(node, docstring, members, parent)
