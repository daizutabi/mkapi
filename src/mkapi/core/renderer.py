"""
This module provides Renderer class that renders Node instance
to create API documentation.
"""
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.core import linker
from mkapi.core.base import Docstring, Section
from mkapi.core.code import Code
from mkapi.core.module import Module
from mkapi.core.node import Node
from mkapi.core.structure import Object


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

    def render(self, node: Node, filters: List[str] = None) -> str:
        """Returns a rendered HTML for Node.

        Args:
            node: Node instance.
        """
        object = self.render_object(node.object, filters=filters)
        docstring = self.render_docstring(node.docstring, filters=filters)
        members = [self.render(member, filters) for member in node.members]
        return self.render_node(node, object, docstring, members)

    def render_node(
        self, node: Node, object: str, docstring: str, members: List[str]
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

    def render_object(self, object: Object, filters: List[str] = None) -> str:
        """Returns a rendered HTML for Object.

        Args:
            object: Object instance.
            filters: Filters.
        """
        if filters is None:
            filters = []
        context = linker.resolve_object(object.html)
        level = context.get("level")
        if level:
            if object.kind in ["module", "package"]:
                filters.append("plain")
            elif "plain" in filters:
                del filters[filters.index("plain")]
            tag = f"h{level}"
        else:
            tag = "div"
        template = self.templates["object"]
        return template.render(context, object=object, tag=tag, filters=filters)

    def render_object_member(
        self, name: str, url: str, signature: Dict[str, Any]
    ) -> str:
        """Returns a rendered HTML for Object in toc.

        Args:
            name: Object name.
            url: Link to definition.
            signature: Signature.
        """
        template = self.templates["member"]
        return template.render(name=name, url=url, signature=signature)

    def render_docstring(self, docstring: Docstring, filters: List[str] = None) -> str:
        """Returns a rendered HTML for Docstring.

        Args:
            docstring: Docstring instance.
        """
        if not docstring:
            return ""
        template = self.templates["docstring"]
        for section in docstring.sections:
            if section.items:
                valid = any(item.description for item in section.items)
                if filters and "strict" in filters or section.name == "Bases" or valid:
                    section.html = self.render_section(section, filters)
        return template.render(docstring=docstring)

    def render_section(self, section: Section, filters: List[str] = None) -> str:
        """Returns a rendered HTML for Section.

        Args:
            section: Section instance.
        """
        if filters is None:
            filters = []
        if section.name == "Bases":
            return self.templates["bases"].render(section=section)
        else:
            return self.templates["items"].render(section=section, filters=filters)

    def render_module(self, module: Module, filters: List[str] = None) -> str:
        """Returns a rendered Markdown for Module.

        Args:
            module: Module instance.
            filters: A list of filters. Avaiable filters: `upper`, `inherit`,
                `strict`, `heading`.

        Note:
            This function returns Markdown instead of HTML. The returned Markdown
            will be converted into HTML by MkDocs. Then the HTML is rendered into HTML
            again by other functions in this module.
        """
        if filters is None:
            filters = []
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

    def render_code(self, code: Code, filters: List[str] = None) -> str:
        if filters is None:
            filters = []
        template = self.templates["code"]
        return template.render(code=code, module=code.module, filters=filters)


#: Renderer instance that can be used globally.
renderer: Renderer = Renderer()
