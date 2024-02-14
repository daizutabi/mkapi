"""importlib module."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.docstrings
from mkapi.globals import get_all, get_fullname
from mkapi.inspect import is_dataclass, iter_dataclass_parameters
from mkapi.items import Item, Name, Section, Text, Type
from mkapi.objects import (
    Attribute,
    Class,
    Function,
    Module,
    create_module,
    is_empty,
    iter_objects,
    objects,
)
from mkapi.utils import cache, del_by_name, get_by_name, get_module_node_source, iter_parent_module_names

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


@cache
def load_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if not (node_source := get_module_node_source(name)):
        return None

    module = create_module(name, *node_source)

    for cls in module.classes:
        _postprocess_class(cls)

    _postprocess_module(module)

    return module


def get_object(fullname: str, skip: str | None = None) -> Module | Class | Function | Attribute | None:
    """Return an [Object] instance by the fullname."""
    if fullname in objects:
        return objects[fullname]

    for name in iter_parent_module_names(fullname):
        if name != skip and load_module(name) and fullname in objects:
            return objects[fullname]

    objects[fullname] = None
    return None


# def _postprocess(obj: Module | Class) -> None:
#     if isinstance(obj, Class):
#         _postprocess_class(obj)

#     for cls in obj.classes:
#         _postprocess(cls)

#     if isinstance(obj, Module):
#         _postprocess_module(obj)


def _postprocess_class(cls: Class) -> None:
    for child in cls.classes:
        _postprocess_class(child)

    inherit_base_classes(cls)

    if init := get_by_name(cls.functions, "__init__"):
        cls.parameters = init.parameters
        cls.raises = init.raises
        cls.doc = mkapi.docstrings.merge(cls.doc, init.doc)
        del_by_name(cls.functions, "__init__")

    if is_dataclass(cls):
        cls.parameters = list(iter_dataclass_parameters(cls))


def iter_base_classes(cls: Class) -> Iterator[Class]:
    """Yield base classes.

    This function is called in postprocess for inheritance.
    """
    if not cls.module:
        return

    for node in cls.node.bases:
        name = next(mkapi.ast.iter_identifiers(node))

        if fullname := get_fullname(name, cls.module.name.str):
            base = get_object(fullname)

            if base and isinstance(base, Class):
                yield base


def inherit_base_classes(cls: Class) -> None:
    """Inherit objects from base classes."""
    # TODO: fix InitVar, ClassVar for dataclasses.
    bases = list(iter_base_classes(cls))

    for name in ["attributes", "functions", "classes"]:
        members = {member.name.str: member for member in getattr(cls, name)}

        for base in bases:
            for member in getattr(base, name):
                members.setdefault(member.name.str, member)

        setattr(cls, name, list(members.values()))


def _postprocess_module(module: Module) -> None:
    for name, fullname in get_all(module.name.str).items():
        obj = get_object(fullname, module.name.str)

        asname = f"{module.name.str}.{name}"
        objects[asname] = obj

        # TODO: asname
        if isinstance(obj, Module):
            module.modules.append(obj)
        elif isinstance(obj, Class):
            module.classes.append(obj)
        elif isinstance(obj, Function):
            module.functions.append(obj)
        elif isinstance(obj, Attribute):
            module.attributes.append(obj)

    add_sections(module)


def add_sections(module: Module) -> None:
    """Add sections."""
    for obj in iter_objects(module):
        if isinstance(obj, Module | Class):
            add_section(obj, obj.classes, "Classes")

        if isinstance(obj, Module | Class | Function):
            name = "Methods" if isinstance(obj, Class) else "Functions"
            add_section(obj, obj.functions, name)

        if isinstance(obj, Module | Class):
            add_section_attributes(obj)


def add_section(
    obj: Module | Class | Function,
    children: Iterable[Class | Function | Attribute],
    name: str,
) -> None:
    """Add Section."""
    if get_by_name(obj.doc.sections, name):
        return

    if items := [_get_item(child) for child in children if not is_empty(child)]:
        section = Section(Name(name), Type(), Text(), items)
        obj.doc.sections.append(section)


def add_section_attributes(obj: Module | Class) -> None:
    """Add an Attributes section."""

    items = []
    attributes = []

    for attr in obj.attributes:
        if attr.doc.sections:
            items.append(_get_item(attr))
        elif not is_empty(attr):
            item = Item(attr.name, attr.type, attr.doc.text)
            items.append(item)
            continue

        attributes.append(attr)

    obj.attributes = attributes

    if not items:
        return

    name = "Attributes"
    sections = obj.doc.sections

    if section := get_by_name(sections, name):
        index = sections.index(section)
        obj.doc.sections[index] = section
    else:
        section = Section(Name(name), Type(), Text(), items)
        obj.doc.sections.append(section)


def _get_item(obj: Module | Class | Function | Attribute) -> Item:
    text = Text(obj.doc.text.str)
    text.markdown = obj.doc.text.markdown.split("\n\n")[0]  # summary line
    type_ = obj.type if isinstance(obj, Attribute) else Type()
    return Item(obj.name, type_, text)


def get_source(obj: Module | Class | Function) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        return obj.source

    if (module := obj.module) and (source := module.source):
        start, stop = obj.node.lineno - 1, obj.node.end_lineno
        return "\n".join(source.splitlines()[start:stop])

    return None
