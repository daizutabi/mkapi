"""Renderer class."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

import mkapi
from mkapi.inspect import get_signature
from mkapi.objects import Attribute, Class, Function, Module

templates: dict[str, Template] = {}


def load_templates(path: Path | None = None) -> None:
    """Load templates."""
    if not path:
        path = Path(mkapi.__file__).parent / "templates"
    loader = FileSystemLoader(path)
    env = Environment(loader=loader, autoescape=True)
    for name in os.listdir(path):
        templates[Path(name).stem] = env.get_template(name)


def render(
    obj: Module | Class | Function | Attribute,
    level: int,
    filters: list[str],
    *,
    is_source: bool = False,
) -> str:
    """Return a rendered Markdown."""
    heading = f"h{level}" if level else "p"
    # fullname = get_markdown(obj.fullname.str)
    names = [x.replace("_", "\\_") for x in obj.qualname.str.split(".")]
    if isinstance(obj, Module):
        qualnames = [[x, "name"] for x in names]
    else:
        qualnames = [[x, "prefix"] for x in names]
        qualnames[-1][1] = "name"
    context = {
        "heading": heading,
        # "fullname": fullname,
        "qualnames": qualnames,
        "obj": obj,
        "doc": obj.doc,
        "filters": filters,
    }
    if isinstance(obj, Module) and is_source:
        return _render_source(obj, context, filters)
    return _render_object(obj, context)


def _render_object(
    obj: Module | Class | Function | Attribute,
    context: dict[str, Any],
) -> str:
    if isinstance(obj, Class | Function):
        context["signature"] = get_signature(obj)
    return templates["object"].render(context)


def get_object_filter_for_source(
    obj: Module | Class | Function | Attribute,
    module: Module,
) -> str | None:
    """Return a filter for an object used in source code pages."""
    if isinstance(obj, Module):
        return f"__mkapi__:{obj.fullname.str}=0"
    if obj.module.name.str == module.name.str and obj.node:
        return f"__mkapi__:{obj.fullname.str}={obj.node.lineno-1}"
    return None


def _render_source(obj: Module, context: dict[str, Any], filters: list[str]) -> str:
    if source := obj.source:
        lines = source.splitlines()
        for filter_ in filters:
            if filter_.startswith("__mkapi__:"):
                name, index_str = filter_[10:].split("=")
                index = int(index_str)
                if len(lines[index]) > 80 and index:  # noqa: PLR2004
                    index -= 1
                line = lines[index]
                if "## __mkapi__." not in line:
                    lines[index] = f"{line}## __mkapi__.{name}"
        source = "\n".join(lines)
    else:
        source = ""
    context["source"] = source
    return templates["source"].render(context)


# def add_sections(module: Module) -> None:
#     """Add sections."""
#     for obj in iter_objects(module):
#         if isinstance(obj, Module | Class):
#             add_section(obj, obj.classes, "Classes")

#         if isinstance(obj, Module | Class | Function):
#             name = "Methods" if isinstance(obj, Class) else "Functions"
#             add_section(obj, obj.functions, name)

#         # if isinstance(obj, Module | Class):
#         #     add_section_attributes(obj)


# def add_section(
#     obj: Module | Class | Function,
#     children: Iterable[Class | Function | Attribute],
#     name: str,
# ) -> None:
#     """Add Section."""
#     if get_by_name(obj.doc.sections, name):
#         return

#     if items := [_get_item(child) for child in children if not is_empty(child)]:
#         section = Section(Name(name), Type(), Text(), items)
#         obj.doc.sections.append(section)


# def add_section_attributes(obj: Module | Class) -> None:
#     """Add an Attributes section."""

#     items = []
#     attributes = []

#     for attr in obj.attributes:
#         if attr.doc.sections:
#             items.append(_get_item(attr))
#         elif not is_empty(attr):
#             item = Item(attr.name, attr.type, attr.doc.text)
#             items.append(item)
#             continue

#         attributes.append(attr)

#     obj.attributes = attributes

#     if not items:
#         return

#     name = "Attributes"
#     sections = obj.doc.sections

#     if section := get_by_name(sections, name):
#         index = sections.index(section)
#         section.items = items
#         obj.doc.sections[index] = section
#     else:
#         section = Section(Name(name), Type(), Text(), items)
#         obj.doc.sections.append(section)


# def _get_item(obj: Module | Class | Function | Attribute) -> Item:
#     text = Text(obj.doc.text.str)
#     text.markdown = obj.doc.text.markdown.split("\n\n")[0]  # summary line
#     type_ = obj.type if isinstance(obj, Attribute) else Type()
#     return Item(obj.name, type_, text)
