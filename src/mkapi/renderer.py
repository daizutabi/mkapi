"""Renderer class."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

from jinja2 import Environment, FileSystemLoader, Template

import mkapi
from mkapi.doc import Doc, create_summary_item
from mkapi.object import (
    Attribute,
    Class,
    Function,
    Module,
    get_source,
    is_child,
    iter_objects,
)
from mkapi.parser import Parser

# is_empty,
# is_member,
# iter_objects,

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from mkapi.object import Object
    from mkapi.parser import Name

templates: dict[str, Template] = {}


def load_templates(path: Path | None = None) -> None:
    """Load templates."""
    if not path:
        path = Path(mkapi.__file__).parent / "templates"

    loader = FileSystemLoader(path)
    env = Environment(loader=loader, autoescape=True)

    for name in os.listdir(path):
        templates[Path(name).stem] = env.get_template(name)


class TemplateKind(Enum):
    HEADING = "heading"
    HEADER = "header"
    OBJECT = "object"
    DOCUMENT = "document"
    SOURCE = "source"


def render(
    obj: Object,
    level: int,
    namespace: str,
    predicate: Callable[[Parser, TemplateKind], bool] | None = None,
) -> str:
    """Return a rendered Markdown."""
    if not (parser := Parser.create(obj.fullname)):
        return f"!!! failure\n\n    {obj.fullname!r} not found."

    markdowns = []

    name = parser.parse_name()
    if level and (not predicate or predicate(parser, TemplateKind.HEADING)):
        markdowns.append(render_heading(name.id, name.fullname, level))

    # if not predicate or predicate(parser, TemplateKind.HEADER):
    #     markdowns.append(render_header(name.id, name.fullname, namespace))

    if not predicate or predicate(parser, TemplateKind.OBJECT):
        signature = parser.parse_signature()
        markdowns.append(render_object(obj, name, namespace, signature))

    if not predicate or predicate(parser, TemplateKind.DOCUMENT):
        doc = parser.parse_doc()
        markdowns.append(render_document(doc))

    #     if isinstance(obj, Module | Class) and (doc := _create_summary_docstring(obj)):
    #         set_markdown(obj, doc)
    #         markdowns.append(render_document(doc))

    if not predicate or predicate(parser, TemplateKind.SOURCE):
        markdowns.append(render_source(obj))

    return "\n\n".join(markdowns)


def render_heading(id_: str, fullname: str, level: int) -> str:
    return templates["heading"].render(id=id_, fullname=fullname, level=level)


def render_object(
    obj: Object,
    name: Name,
    namespace: str,
    signature: list[tuple[str, str]],
) -> str:
    if isinstance(obj, Module):
        names = [[x, "name"] for x in name.names]
    else:
        names = [[x, "prefix"] for x in name.names]
        names[-1][1] = "name"

    return templates["object"].render(
        obj=obj,
        id=name.id,
        namespace=namespace,
        names=names,
        signature=signature,
    )


def render_document(doc: Doc) -> str:
    return templates["document"].render(doc=doc)


def render_source(obj: Object, attr: str = "") -> str:
    if source := _get_source(obj):
        source = source.rstrip()
        return templates["source"].render(source=source, attr=attr) + "\n"

    return ""


def _get_source(obj: Object, *, skip_self: bool = True) -> str:
    if not (source := get_source(obj)) or not obj.node:
        return ""
    lines = source.splitlines()
    start = 1 if isinstance(obj, Module) else obj.node.lineno
    module = obj.name if isinstance(obj, Module) else obj.module

    for child in iter_objects(obj):
        if skip_self and child is obj or isinstance(obj, Attribute) or not child.node:
            continue

        if isinstance(child, Module):
            index = 0

        elif child != obj and (not is_child(child, obj) or child.module is not module):
            continue

        else:
            index = child.node.lineno - start

        if len(lines[index]) > 80 and index:  # noqa: PLR2004
            index -= 1

        line = lines[index]
        if "## __mkapi__." not in line:
            lines[index] = f"{line}## __mkapi__.{child.fullname}"

    return "\n".join(lines)


# def _create_summary_docstring(obj: Module | Class) -> Doc | None:
#     if sections := list(_iter_summary_sections(obj)):
#         return Doc(Name(), Type(), Text(), sections)
#     return None


# def _iter_summary_sections(obj: Module | Class) -> Iterator[Section]:
#     """Add sections."""
#     if section := _create_summary_section(obj.classes, "Classes"):
#         yield section

#     name = "Methods" if isinstance(obj, Class) else "Functions"
#     if section := _create_summary_section(obj.functions, name):
#         yield section


# def _create_summary_section(
#     children: Iterable[Class | Function],
#     name: str,
# ) -> Section | None:
#     items = []
#     for child in children:
#         if not is_empty(child):
#             item = create_summary_item(child.name, child.doc)
#             items.append(item)

#     if items:
#         return Section(Name(name), Type(), Text(), items)

#     return None
