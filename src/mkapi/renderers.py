"""Renderer class."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

from jinja2 import Environment, FileSystemLoader, Template

import mkapi
from mkapi.docstrings import Docstring, create_summary_item
from mkapi.items import Name, Section, Text, Type
from mkapi.link import set_markdown
from mkapi.objects import Attribute, Class, Function, Module, get_source, is_empty, is_member, iter_objects
from mkapi.signatures import get_signature

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

templates: dict[str, Template] = {}


def load_templates(path: Path | None = None) -> None:
    """Load templates."""
    if not path:
        path = Path(mkapi.__file__).parent / "templates"
    loader = FileSystemLoader(path)
    env = Environment(loader=loader, autoescape=True)
    for name in os.listdir(path):
        templates[Path(name).stem] = env.get_template(name)


Object: TypeAlias = Module | Class | Function | Attribute


def render_heading(obj: Object, level: int, cls: str = "mkapi-heading") -> str:
    id_ = obj.fullname.str
    name = obj.fullname.str.replace("_", "\\_")
    context = {"level": level, "id": id_, "class": cls, "name": name}
    return templates["heading"].render(context)


def render_header(obj: Object, namespace: str) -> str:
    return templates["header"].render(obj=obj, namespace=namespace)


def render_object(obj: Object) -> str:
    names = [x.replace("_", "\\_") for x in obj.qualname.str.split(".")]

    if isinstance(obj, Module):
        qualnames = [[x, "name"] for x in names]
    else:
        qualnames = [[x, "prefix"] for x in names]
        qualnames[-1][1] = "name"

    signature = None if isinstance(obj, Module) else get_signature(obj)

    return templates["object"].render(obj=obj, qualnames=qualnames, signature=signature)


def render_document(doc: Docstring) -> str:
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
    module = obj if isinstance(obj, Module) else obj.module

    for child in iter_objects(obj):
        if skip_self and child is obj or isinstance(obj, Attribute) or not child.node:
            continue
        if isinstance(child, Module):
            index = 0
        elif child != obj and (not is_member(child, obj) or child.module is not module):
            continue
        else:
            index = child.node.lineno - start
        if len(lines[index]) > 80 and index:  # noqa: PLR2004
            index -= 1

        line = lines[index]
        if "## __mkapi__." not in line:
            lines[index] = f"{line}## __mkapi__.{child.fullname.str}"

    return "\n".join(lines)


def render(
    obj: Object,
    level: int,
    namespace: str,
    filters: list[str],  # noqa: ARG001
    predicate: Callable[[str, str], bool] | None = None,
) -> str:
    """Return a rendered Markdown."""
    set_markdown(obj)

    fullname = obj.fullname.str
    markdowns = [render_heading(obj, level) if level else ""]

    if not predicate or predicate(fullname, "header"):
        markdowns.append(render_header(obj, namespace))

    if not predicate or predicate(fullname, "object"):
        markdowns.append(render_object(obj))

    if not predicate or predicate(fullname, "document"):
        markdowns.append(render_document(obj.doc))

        if isinstance(obj, Module | Class) and (doc := _create_summary_docstring(obj)):
            set_markdown(obj, doc)
            markdowns.append(render_document(doc))

    if not predicate or predicate(fullname, "source"):
        markdowns.append(render_source(obj))

    return "\n\n".join(markdowns)


def _create_summary_docstring(obj: Module | Class) -> Docstring | None:
    if sections := list(_iter_summary_sections(obj)):
        return Docstring(Name(), Type(), Text(), sections)
    return None


def _iter_summary_sections(obj: Module | Class) -> Iterator[Section]:
    """Add sections."""
    if section := _create_summary_section(obj.classes, "Classes"):
        yield section

    name = "Methods" if isinstance(obj, Class) else "Functions"
    if section := _create_summary_section(obj.functions, name):
        yield section


def _create_summary_section(children: list[Class] | list[Function], name: str) -> Section | None:
    items = []
    for child in children:
        if not is_empty(child):
            item = create_summary_item(child.name, child.doc)
            items.append(item)

    if items:
        return Section(Name(name), Type(), Text(), items)

    return None
