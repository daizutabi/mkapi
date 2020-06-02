import os
from dataclasses import dataclass, field
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi


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

    def render(self, node, parent=None) -> str:
        docstring = self.render_docstring(node.docstring)
        members = []
        if node.members:
            members = [self.render(member, node) for member in node.members]
        return self.render_node(node, docstring, members, parent)

    def render_node(self, node, docstring: str, members: List[str], parent) -> str:
        template = self.templates["node"]
        return template.render(
            node=node, docstring=docstring, members=members, parent=parent
        )

    def render_docstring(self, docstring) -> str:
        if docstring is None:
            return ""
        template = self.templates["docstring"]
        for section in docstring.sections:
            if section.items:
                section.html = self.render_section(section)
        return template.render(docstring=docstring)

    def render_code(self, code: str) -> str:
        template = self.templates["code"]
        return template.render(code=code)

    def render_section(self, section) -> str:
        if section.name in ["Parameters", "Attributes", "Raises"]:
            return self.templates["args"].render(section=section)
        else:
            raise ValueError(f"Invalid section name: {section.name}")
