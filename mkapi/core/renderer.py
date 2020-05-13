import os
from dataclasses import dataclass, field
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.core.inspect import Node


@dataclass
class Renderer:
    name: str = ""
    templates: Dict[str, Template] = field(default_factory=dict, init=False)

    def __post_init__(self):
        path = os.path.join(os.path.dirname(mkapi.__file__), "templates")
        loader = FileSystemLoader(path)
        env = Environment(loader=loader, autoescape=select_autoescape(["jinja2"]))
        for name in os.listdir(path):
            template = env.get_template(name)
            name = os.path.splitext(name)[0]
            self.templates[name] = template
        if len(self.templates) == 1:
            self.name = name

    def render_node(self, node: Node, members: List[str]) -> str:
        template = self.templates[self.name]
        return template.render(node=node, members=members)

    def render(self, node):
        print(node.name)
        members = []
        if node.members:
            members = [self.render(member) for member in node.members]
        return self.render_node(node, members)
