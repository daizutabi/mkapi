"""Renderer class."""
from __future__ import annotations

import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

import mkapi
from mkapi.importlib import get_object
from mkapi.objects import iter_objects_with_depth

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkapi.objects import Class, Function, Module

templates: dict[str, Template] = {}


def load_templates(path: Path | None = None) -> None:
    """Load templates."""
    if not path:
        path = Path(mkapi.__file__).parent / "templates"
    loader = FileSystemLoader(path)
    env = Environment(loader=loader, autoescape=select_autoescape(["jinja2"]))
    for name in os.listdir(path):
        templates[Path(name).stem] = env.get_template(name)


NAME_PATTERN = re.compile(r"^(.+?)(\.\*+)?$")


def _split_name_depth(name: str) -> tuple[str, int]:
    if m := NAME_PATTERN.match(name):
        depth = m.group(2) or "."
        return m.group(1), int(len(depth)) - 1
    return name, 0


def _render_markdown(name: str, level: int, filters: str) -> str:
    heading = "#" * level + " " if level else ""
    return f"{heading}::: {name}{filters}\n"


def render_markdown(
    name: str,
    level: int,
    filters: list[str],
    predicate: Callable[[Module | Class | Function], bool] | None = None,
) -> str:
    """Return a rendered Markdown for an object.

    Optionally, only return objects that satisfy a given predicate.

    Note:
        This function returns Markdown instead of HTML. The returned Markdown
        will be converted into HTML by MkDocs. Then the HTML is rendered into HTML
        again by other functions in this module.
    """
    filters_ = "|" + "|".join(filters) if filters else ""
    name, maxdepth = _split_name_depth(name)
    if not (obj := get_object(name)):
        return f"{name!r} not found.\n"
    markdowns = []
    for obj_, depth in iter_objects_with_depth(obj, maxdepth):
        if predicate and not predicate(obj_):
            continue
        level_ = level + depth if level else 0
        markdowns.append(_render_markdown(obj_.fullname, level_, filters_))
    return "\n".join(markdowns)

    # if suffix == 1:
    #     members = [obj.classes + obj.functions]
    #     m

    # obj =
    # if name.endswith(".*"):
    #     name = name[:-2]
    #     members =
    #     markdowns = []
    #     for markdown i
    # heading = "#" * level + " " if level else ""
    # markdown = f"{heading}::: {name}{filters_}"
    # return _render_markdown(name, level, filters_)
    # if not (module := load_module(name)):
    #     return f"{name} not found"
    # # module_filter = object_filter = ""
    # # if filters:
    # #     object_filter = "|" + "|".join(filters)
    # # template = self.templates["module"]
    # return templates["module"].render(
    #     module=module,
    #     # module_filter=module_filter,
    #     # object_filter=object_filter,
    # )


def render(obj: Module | Class | Function, level: int, filters: list[str]) -> str:
    """Return a rendered HTML for Node.

    Args:
        obj: Object instance.
        level: Heading level.
        filters: Filters.
    """
    obj_str = render_object(obj, filters=filters)
    return obj_str
    doc_str = render_docstring(obj.doc, filters=filters)
    members = []
    for member in obj.classes + obj.functions:
        member_str = render(member, level + 1, filters)
        members.append(member_str)
    return templates["node"].render(obj=obj_str, doc=doc_str, members=members)


def render_object(obj: Module | Class | Function, filters: list[str]) -> str:
    """Return a rendered HTML for Object.

    Args:
        obj: Object instance.
        filters: Filters.
    """
    # context = resolve_object(obj.html)
    # level = context.get("level")
    # if level:
    #     if obj.kind in ["module", "package"]:
    #         filters.append("plain")
    #     elif "plain" in filters:
    #         del filters[filters.index("plain")]
    #     tag = f"h{level}"
    # else:
    #     tag = "div"
    # template = self.templates["object"]
    # return template.render(context, object=obj, tag=tag, filters=filters)

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


class ObjectParser(HTMLParser):  # noqa: D101
    def feed(self, html: str) -> dict[str, int | str]:  # noqa: D102
        self.context = {"href": [], "heading_id": ""}
        super().feed(html)
        href = self.context["href"]
        if len(href) == 2:
            prefix_url, name_url = href
        elif len(href) == 1:
            prefix_url, name_url = "", href[0]
        else:
            prefix_url, name_url = "", ""
        self.context["prefix_url"] = prefix_url
        self.context["name_url"] = name_url
        del self.context["href"]
        return self.context

    def handle_starttag(self, tag: str, attrs: list) -> None:  # noqa: D102
        context = self.context
        if tag == "p":
            context["level"] = 0
        elif re.match(r"h[1-6]", tag):
            context["level"] = int(tag[1:])
            for attr in attrs:
                if attr[0] == "id":
                    self.context["heading_id"] = attr[1]
        elif tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    href = attr[1]
                    if href.startswith("./"):
                        href = href[2:]
                    self.context["href"].append(href)


parser = ObjectParser()


def resolve_object(html: str) -> dict[str, int | str]:
    """Reutrns an object context dictionary.

    Args:
        html: HTML source.

    Examples:
        >>> resolve_object("<p><a href='a'>p</a><a href='b'>n</a></p>")
        {'heading_id': '', 'level': 0, 'prefix_url': 'a', 'name_url': 'b'}
        >>> resolve_object("<h2 id='i'><a href='a'>p</a><a href='b'>n</a></h2>")
        {'heading_id': 'i', 'level': 2, 'prefix_url': 'a', 'name_url': 'b'}
    """
    parser.reset()
    return parser.feed(html)
