"""
This module provides Renderer class that renders Node instance
to create API documentation.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.core import linker
from mkapi.core.base import Docstring, Object, Section
from mkapi.core.module import Module
from mkapi.core.node import Node


@dataclass
class Renderer:
    """Renderer instance renders Node instance recursively to create
    API documentation.

    Attributes:
        templates: Jinja template dictionary.
    """

    templates: Dict[str, Template] = field(default_factory=dict, init=False)

    def __post_init__(self):
        path = os.path.join(os.path.dirname(mkapi.__file__), "templates")
        loader = FileSystemLoader(path)
        env = Environment(loader=loader, autoescape=select_autoescape(["jinja2"]))
        for name in os.listdir(path):
            template = env.get_template(name)
            name = os.path.splitext(name)[0]
            self.templates[name] = template

    def render(self, node: Node, upper: bool = False) -> str:
        """Returns a rendered HTML for Node.

        Args:
            node: Node instance.
            upper: If True, object is written in upper case letters.
        """
        heading = node.parent is None
        object = self.render_object(node.object, heading=heading, upper=upper)
        docstring = self.render_docstring(node.docstring)
        # if node.parent is None:
        #     objects = [member.object for member in node.members]
        #     objects = self.render_objects(objects)
        # else:
        #     objects = ""
        objects = ""
        members = [self.render(member) for member in node.members]
        return self.render_node(node, object, docstring, objects, members)

    def render_node(
        self, node: Node, object: str, docstring: str, objects: str, members: List[str]
    ) -> str:
        """Returns a rendered HTML for Node using prerendered components.

        Args:
            node: Node instance.
            object: Rendered HTML for Object instance.
            docstring: Rendered HTML for Docstring instance.
            members: A list of rendered HTML for member Node instances.
        """
        template = self.templates["node"]
        return template.render(
            node=node, object=object, docstring=docstring, members=members
        )

    def render_object(
        self,
        object: Object,
        heading: bool = False,
        upper: bool = False,
        internal_link: bool = False,
    ) -> str:
        """Returns a rendered HTML for Object.

        Args:
            object: Object instance.
            heading: If True, object is written in a heading tag.
            upper: If True, object is written in upper case letters.
        """
        context = linker.resolve_object(object.html)
        if internal_link:
            context["prefix_url"] = "#" + object.prefix
            context["name_url"] = "#" + object.id
            if context["level"]:
                context["level"] += 1

        if context["level"] and heading:
            template = self.templates["object_heading"]
        else:
            template = self.templates["object_div"]
        html = template.render(context, object=object, upper=upper)
        return html

    def render_docstring(self, docstring: Docstring) -> str:
        """Returns a rendered HTML for Docstring.

        Args:
            docstring: Docstring instance.
        """
        if docstring is None:
            return ""
        template = self.templates["docstring"]
        for section in docstring.sections:
            if section.items:
                section.html = self.render_section(section)
        return template.render(docstring=docstring)

    def render_section(self, section: Section) -> str:
        """Returns a rendered HTML for Section.

        Args:
            section: Section instance.
        """
        if section.name in ["Parameters", "Attributes", "Raises"]:
            return self.templates["args"].render(section=section)
        elif section.name == "Bases":
            return self.templates["bases"].render(section=section)
        else:
            raise ValueError(f"Invalid section name: {section.name}")

    def render_module(self, module: Module, filters: List[str]) -> str:
        """Returns a rendered Markdown for Module.

        Args:
            module: Module instance.
            filters: A list of filters. Avaiable filters: `upper`, `inherit`,
                `strict`.

        Note:
            This function returns Markdown instead of HTML. The returned Markdown
            will be converted into HTML by MkDocs. Then the HTML is rendered into HTML
            again by other functions in this module.
        """
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


#: Renderer instance that can be used globally.
renderer: Renderer = Renderer()
