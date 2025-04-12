"""Render documentation for Python objects."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from astdoc.object import (
    Attribute,
    Class,
    Function,
    Module,
    Property,
    get_source,
    is_child,
    iter_objects,
)
from jinja2 import Environment, FileSystemLoader, Template

import mkapi
from mkapi.parser import Parser

if TYPE_CHECKING:
    from collections.abc import Callable

    from astdoc.doc import Doc
    from astdoc.object import Object

    from mkapi.parser import NameSet

templates: dict[str, Template] = {}


def load_templates(path: Path | None = None) -> None:
    """Load Jinja2 templates from the specified directory.

    Initialize the `templates` dictionary with Jinja2 templates
    loaded from the given directory path. If no path is provided, it defaults
    to the "templates" directory located in the same directory as the mkapi
    module.

    Args:
        path (Path | None): The directory path from which to load the templates.
            If None, defaults to the "templates" directory in the mkapi module.

    Returns:
        None

    """
    if not path:
        path = Path(mkapi.__file__).parent / "templates"

    loader = FileSystemLoader(path)
    env = Environment(loader=loader, autoescape=True)

    for name in path.iterdir():
        templates[name.stem] = env.get_template(name.name)


class TemplateKind(Enum):
    """Enum representing different types of templates."""

    HEADING = "heading"
    HEADER = "header"
    OBJECT = "object"
    DOCUMENT = "document"
    SOURCE = "source"


def render(
    name: str,
    module: str | None,
    level: int,
    namespace: str,
    predicate: Callable[[Parser, TemplateKind], bool] | None = None,
) -> str:
    """Render a template with the given parameters.

    Render a template based on the provided name, level, namespace,
    and an optional predicate function. Process the template using the
    appropriate rendering functions for headings, objects, documents, and source
    code, depending on the predicate's evaluation.

    Args:
        name (str): The name of the object to render.
        module (str | None): The module of the object to render.
        level (int): The heading level to use for rendering headings.
        namespace (str): The namespace to use for rendering objects.
        predicate (Callable[[Parser, TemplateKind], bool] | None, optional):
            A function that takes a `Parser` instance and a `TemplateKind` enum
            value, and returns a boolean indicating whether to render the
            corresponding template section. Defaults to None.

    Returns:
        str: The rendered markdown string.

    """
    if not (parser := Parser.create(name, module)):
        if module:
            return f"!!! failure\n\n    {name!r} not found in {module!r}."

        return f"!!! failure\n\n    {name!r} not found."

    markdowns = []

    name_set = parser.parse_name_set()
    if level and (not predicate or predicate(parser, TemplateKind.HEADING)):
        markdowns.append(render_heading(name_set, level))

    if not predicate or predicate(parser, TemplateKind.OBJECT):
        signature = parser.parse_signature()
        markdowns.append(render_object(name_set, level, namespace, signature))

    if not predicate or predicate(parser, TemplateKind.DOCUMENT):
        doc = parser.parse_doc()
        bases = parser.parse_bases()
        markdowns.append(render_document(doc, bases))

    if not predicate or predicate(parser, TemplateKind.SOURCE):
        markdowns.append(render_source(parser.obj))

    return "\n\n".join(markdowns)


def render_heading(name_set: NameSet, level: int) -> str:
    """Render a heading for the specified object.

    Render a heading for the specified object using the provided ID, fullname,
    and level. Use the "heading" template to generate the heading.

    Args:
        name_set (NameSet): The name set containing the object's ID and fullname.
        level (int): The heading level to use for rendering headings.

    Returns:
        str: The rendered heading as a markdown string.

    """
    return templates["heading"].render(
        id=name_set.id,
        fullname=name_set.fullname,
        level=level,
    )


def render_object(
    name_set: NameSet,
    level: int,
    namespace: str,
    signature: list[tuple[str, str]],
) -> str:
    """Render an object entry using the specified parameters.

    Render an object entry using the provided object, name set, namespace,
    signature, and bases. Use the "object" template to generate the object entry.

    Args:
        name_set (NameSet): The name set containing the object's ID and fullname.
        level (int): The heading level to use for rendering headings.
        namespace (str): The namespace to use for rendering objects.
        signature (list[tuple[str, str]]): The signature of the object.

    Returns:
        str: The rendered object entry as a markdown string.

    """
    return templates["object"].render(
        kind=name_set.kind,
        name=name_set.name,
        parent=name_set.parent,
        module=name_set.module,
        fullname=name_set.fullname,
        id=name_set.id,
        obj_id=name_set.obj_id,
        parent_id=name_set.parent_id,
        level=level,
        namespace=namespace,
        signature=signature,
        type_params=name_set.type_params,
    )


def render_document(doc: Doc, bases: list[str]) -> str:
    """Render a document using the specified parameters.

    Render a document using the provided document. Use the "document" template
    to generate the document.

    Args:
        doc (Doc): The document to render.
        bases (list[str]): The bases of the object.

    Returns:
        str: The rendered document as a markdown string.

    """
    return templates["document"].render(doc=doc, bases=bases)


def render_source(obj: Object, attr: str = "") -> str:
    """Render the source code for the specified object.

    Render the source code for the specified object using the provided object
    and attribute name. Use the "source" template to generate the source code.

    Args:
        obj (Object): The object to render.
        attr (str): The attribute name to render.

    Returns:
        str: The rendered source code as a markdown string.

    """
    if not isinstance(obj, Module | Class | Function | Attribute | Property):
        return ""

    if source := _get_source(obj):
        source = source.rstrip()
        start = 1 if isinstance(obj, Module) else obj.node.lineno
        attr = f'linenums="{start}"'
        backticks = "`" * max(find_max_backticks(source) + 1, 3)
        template = templates["source"]
        return template.render(source=source, attr=attr, backticks=backticks) + "\n"

    return ""


def find_max_backticks(source_code: str) -> int:
    """Find the maximum number of consecutive backticks in the source code.

    Args:
        source_code (str): The source code to search.

    Returns:
        int: The maximum number of consecutive backticks.

    """
    pattern = r"`+"
    matches = re.findall(pattern, source_code)
    if not matches:
        return 0

    return max(len(match) for match in matches)


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

    names = set()
    for child in iter_objects(obj):
        if child.fullname in names:
            continue

        names.add(child.fullname)

        if not isinstance(child, Class | Function | Attribute | Property):
            continue

        if (
            (skip_self and child is obj)
            or isinstance(obj, Attribute)
            or not child.node
            or (child != obj and (not is_child(child, obj) or child.module != module))
        ):
            continue

        index = child.node.lineno - start

        if len(lines[index]) > 72 and index:
            index -= 1

        line = lines[index]
        if "## __mkapi__." not in line:
            lines[index] = f"{line}## __mkapi__.{child.fullname}"

    return "\n".join(lines)
