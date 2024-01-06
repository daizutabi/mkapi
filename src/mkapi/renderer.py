"""Renderer class."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.objects import Module


@dataclass
class Renderer:
    """Render [Object] instance recursively to create API documentation.

    Attributes:
        templates: Jinja template dictionary.
    """

    templates: dict[str, Template] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        path = Path(mkapi.__file__).parent / "templates"
        loader = FileSystemLoader(path)
        env = Environment(loader=loader, autoescape=select_autoescape(["jinja2"]))
        for name in os.listdir(path):
            template = env.get_template(name)
            self.templates[Path(name).stem] = template

    def render_module(self, module: Module, filters: list[str] | None = None) -> str:
        """Return a rendered Markdown for Module.

        Args:
            module: Module instance.
            filters: A list of filters. Avaiable filters: `inherit`, `strict`,
                `heading`.

        Note:
            This function returns Markdown instead of HTML. The returned Markdown
            will be converted into HTML by MkDocs. Then the HTML is rendered into HTML
            again by other functions in this module.
        """
        filters = filters if filters else []
        module_filter = object_filter = ""
        if filters:
            object_filter = "|" + "|".join(filters)
        template = self.templates["module"]
        return template.render(
            module=module,
            module_filter=module_filter,
            object_filter=object_filter,
        )

    # def render(self, node: Node, filters: list[str] | None = None) -> str:
    #     """Return a rendered HTML for Node.

    #     Args:
    #         node: Node instance.
    #         filters: Filters.
    #     """
    #     obj = self.render_object(node.object, filters=filters)
    #     docstring = self.render_docstring(node.docstring, filters=filters)
    #     members = [self.render(member, filters) for member in node.members]
    #     return self.render_node(node, obj, docstring, members)

    # def render_node(
    #     self,
    #     node: Node,
    #     obj: str,
    #     docstring: str,
    #     members: list[str],
    # ) -> str:
    #     """Return a rendered HTML for Node using prerendered components.

    #     Args:
    #         node: Node instance.
    #         obj: Rendered HTML for Object instance.
    #         docstring: Rendered HTML for Docstring instance.
    #         members: A list of rendered HTML for member Node instances.
    #     """
    #     template = self.templates["node"]
    #     return template.render(
    #         node=node,
    #         object=obj,
    #         docstring=docstring,
    #         members=members,
    #     )

    # def render_object(self, obj: Object, filters: list[str] | None = None) -> str:
    #     """Return a rendered HTML for Object.

    #     Args:
    #         obj: Object instance.
    #         filters: Filters.
    #     """
    #     filters = filters if filters else []
    #     context = link.resolve_object(obj.html)
    #     level = context.get("level")
    #     if level:
    #         if obj.kind in ["module", "package"]:
    #             filters.append("plain")
    #         elif "plain" in filters:
    #             del filters[filters.index("plain")]
    #         tag = f"h{level}"
    #     else:
    #         tag = "div"
    #     template = self.templates["object"]
    #     return template.render(context, object=obj, tag=tag, filters=filters)

    # def render_object_member(
    #     self,
    #     name: str,
    #     url: str,
    #     signature: dict[str, Any],
    # ) -> str:
    #     """Return a rendered HTML for Object in toc.

    #     Args:
    #         name: Object name.
    #         url: Link to definition.
    #         signature: Signature.
    #     """
    #     template = self.templates["member"]
    #     return template.render(name=name, url=url, signature=signature)

    # def render_docstring(
    #     self,
    #     docstring: Docstring,
    #     filters: list[str] | None = None,
    # ) -> str:
    #     """Return a rendered HTML for Docstring.

    #     Args:
    #         docstring: Docstring instance.
    #         filters: Filters.
    #     """
    #     if not docstring:
    #         return ""
    #     template = self.templates["docstring"]
    #     for section in docstring.sections:
    #         if section.items:
    #             valid = any(item.description for item in section.items)
    #             if filters and "strict" in filters or section.name == "Bases" or valid:
    #                 section.html = self.render_section(section, filters)
    #     return template.render(docstring=docstring)

    # def render_section(self, section: Section, filters: list[str] | None = None) -> str:
    #     """Return a rendered HTML for Section.

    #     Args:
    #         section: Section instance.
    #         filters: Filters.
    #     """
    #     filters = filters if filters else []
    #     if section.name == "Bases":
    #         return self.templates["bases"].render(section=section)
    #     return self.templates["items"].render(section=section, filters=filters)

    # def render_code(self, code: Code, filters: list[str] | None = None) -> str:
    #     """Return a rendered Markdown for source code.

    #     Args:
    #         code: Code instance.
    #         filters: Filters.
    #     """
    #     filters = filters if filters else []
    #     template = self.templates["code"]
    #     return template.render(code=code, module=code.module, filters=filters)


#: Renderer instance that is used globally.
renderer: Renderer = Renderer()
