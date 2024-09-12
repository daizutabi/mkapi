"""Provide rendering functions."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, Template

import mkapi
from mkapi.doc import Doc
from mkapi.object import (
    Attribute,
    Class,
    Function,
    Module,
    Property,
    get_source,
    is_child,
    iter_objects,
)
from mkapi.parser import Parser

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkapi.object import Object
    from mkapi.parser import NameSet

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
    name: str,
    level: int,
    namespace: str,
    predicate: Callable[[Parser, TemplateKind], bool] | None = None,
) -> str:
    """Return a rendered Markdown."""
    if not (parser := Parser.create(name)):
        return f"!!! failure\n\n    {name!r} not found."

    markdowns = []

    name_set = parser.parse_name_set()
    if level and (not predicate or predicate(parser, TemplateKind.HEADING)):
        node = name_set.node
        markdowns.append(render_heading(node.id, node.fullname, level))

    if not predicate or predicate(parser, TemplateKind.OBJECT):
        obj = parser.obj
        signature = parser.parse_signature()
        bases = parser.parse_bases()
        markdowns.append(render_object(obj, name_set, namespace, signature, bases))

    if not predicate or predicate(parser, TemplateKind.DOCUMENT):
        doc = parser.parse_doc()
        markdowns.append(render_document(doc))

    if not predicate or predicate(parser, TemplateKind.SOURCE):
        markdowns.append(render_source(parser.obj))

    return "\n\n".join(markdowns)


def render_heading(id_: str, fullname: str, level: int) -> str:
    return templates["heading"].render(id=id_, fullname=fullname, level=level)


def render_object(
    obj: Object,
    name_set: NameSet,
    namespace: str,
    signature: list[tuple[str, str]],
    bases: list[str],
) -> str:
    if isinstance(obj, Module):
        names = [[x, "name"] for x in name_set.node.names]
    else:
        names = [[x, "prefix"] for x in name_set.node.names]
        names[-1][1] = "name"

    return templates["object"].render(
        obj=obj,
        obj_id=name_set.obj.id,
        node_id=name_set.node.id,
        namespace=namespace,
        names=names,
        signature=signature,
        bases=bases,
    )


def render_document(doc: Doc) -> str:
    return templates["document"].render(doc=doc)


def render_source(obj: Object, attr: str = "") -> str:
    if not isinstance(obj, (Module, Class, Function, Attribute, Property)):
        return ""

    if source := _get_source(obj):
        source = source.rstrip()
        return templates["source"].render(source=source, attr=attr) + "\n"

    return ""


def _get_source(
    obj: Module | Class | Function | Attribute | Property,
    *,
    skip_self: bool = True,
) -> str:
    if not (source := get_source(obj)) or not obj.node:
        return ""

    lines = source.splitlines()
    start = 1 if isinstance(obj, Module) else obj.node.lineno
    module = obj.name if isinstance(obj, Module) else obj.module

    # if isinstance(obj, Module) and "## __mkapi__." not in lines[0]:
    #     lines[0] = f"{lines[0]}## __mkapi__.{module}"

    for child in iter_objects(obj):
        if not isinstance(child, (Class, Function, Attribute, Property)):
            continue

        if skip_self and child is obj or isinstance(obj, Attribute) or not child.node:
            continue

        elif child != obj and (not is_child(child, obj) or child.module is not module):
            continue

        else:
            index = child.node.lineno - start

        if len(lines[index]) > 76 and index:
            index -= 1

        line = lines[index]
        if "## __mkapi__." not in line:
            lines[index] = f"{line}## __mkapi__.{child.fullname}"

    return "\n".join(lines)
