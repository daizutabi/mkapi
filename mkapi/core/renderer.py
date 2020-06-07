import os
from dataclasses import dataclass, field
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.core import linker


@dataclass
class Renderer:
    templates: Dict[str, Template] = field(default_factory=dict, init=False)
    upper: bool = False

    def __post_init__(self):
        path = os.path.join(os.path.dirname(mkapi.__file__), "templates")
        loader = FileSystemLoader(path)
        env = Environment(loader=loader, autoescape=select_autoescape(["jinja2"]))
        for name in os.listdir(path):
            template = env.get_template(name)
            name = os.path.splitext(name)[0]
            self.templates[name] = template

    def render(self, node) -> str:
        object = self.render_object(node.object, heading=node.parent is None)
        docstring = self.render_docstring(node.docstring)
        members = []
        if node.members:
            members = [self.render(member) for member in node.members]
        return self.render_node(node, object, docstring, members)

    def render_node(self, node, object, docstring: str, members: List[str]) -> str:
        template = self.templates["node"]
        return template.render(
            node=node, object=object, docstring=docstring, members=members
        )

    def render_object(self, object, heading):
        context = linker.resolve_object(object.html)
        if context["level"] and heading:
            template = self.templates["object_heading"]
        else:
            template = self.templates["object_div"]
        html = template.render(context, object=object, upper=self.upper and heading)
        return html

    def render_docstring(self, docstring) -> str:
        if docstring is None:
            return ""
        template = self.templates["docstring"]
        for section in docstring.sections:
            if section.items:
                section.html = self.render_section(section)
        return template.render(docstring=docstring)

    def render_section(self, section) -> str:
        if section.name in ["Parameters", "Attributes", "Raises"]:
            return self.templates["args"].render(section=section)
        else:
            raise ValueError(f"Invalid section name: {section.name}")

    def render_module(self, module, filters) -> str:
        module_filter = ""
        if "upper" in filters:
            module_filter = "|upper"
            filters = filters.copy()
            del filters[filters.index("upper")]
        object_filter = "|" + "|".join(filters)
        template = self.templates["module"]
        return template.render(
            module=module, module_filter=module_filter, object_filter=object_filter
        )


renderer = Renderer()
