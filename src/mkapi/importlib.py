"""importlib module."""
from __future__ import annotations

import re
from functools import cache
from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.docstrings
from mkapi.globals import get_all, get_fullname
from mkapi.inspect import is_dataclass, iter_dataclass_parameters
from mkapi.items import Attributes, Item, Section, Text, Type
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
from mkapi.utils import (
    del_by_name,
    get_by_name,
    get_by_type,
    get_module_node_source,
    iter_parent_module_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


@cache
def load_module(name: str) -> Module | None:
    """Return a [Module] instance by the name."""
    if not (node_source := get_module_node_source(name)):
        return None
    module = create_module(name, *node_source)
    _postprocess(module)
    return module


def get_object(fullname: str) -> Module | Class | Function | Attribute | None:
    """Return an [Object] instance by the fullname."""
    if fullname in objects:
        return objects[fullname]
    for module_name in iter_parent_module_names(fullname):
        if load_module(module_name) and fullname in objects:
            return objects[fullname]
    objects[fullname] = None
    return None


def get_source(
    obj: Module | Class | Function,
    maxline: int | None = None,
) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        if obj.source:
            return "\n".join(obj.source.splitlines()[:maxline])
        return None
    if (module := obj.module) and (source := module.source):
        start, stop = obj.node.lineno - 1, obj.node.end_lineno
        return "\n".join(source.splitlines()[start:stop][:maxline])
    return None


def _postprocess(obj: Module | Class) -> None:
    if isinstance(obj, Class):
        _postprocess_class(obj)
    for cls in obj.classes:
        _postprocess(cls)
    if isinstance(obj, Module):
        add_sections(obj)


def _postprocess_class(cls: Class) -> None:
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
        if fullname := get_fullname(cls.module.name, name):
            base = get_object(fullname)
            if base and isinstance(base, Class):
                yield base


def inherit_base_classes(cls: Class) -> None:
    """Inherit objects from base classes."""
    # TODO: fix InitVar, ClassVar for dataclasses.
    bases = list(iter_base_classes(cls))
    for name in ["attributes", "functions", "classes"]:
        members = {}
        for base in bases:
            for member in getattr(base, name):
                members[member.name] = member
        for member in getattr(cls, name):
            members[member.name] = member
        setattr(cls, name, list(members.values()))


def add_sections(module: Module) -> None:
    """Add sections."""
    for obj in iter_objects(module):
        if isinstance(obj, Module | Class):
            add_classes(obj)
        if isinstance(obj, Module | Class | Function):
            add_functions(obj)
        if isinstance(obj, Module | Class):
            add_attributes(obj)


def add_classes(obj: Module | Class) -> None:
    """Add classes section."""
    if get_by_name(obj.doc.sections, "Classes"):
        return
    if items := list(_iter_items(obj.classes)):
        section = Section("Classes", Type(), Text(), items)
        obj.doc.sections.append(section)


def add_functions(obj: Module | Class | Function) -> None:
    """Add functions section."""
    if get_by_name(obj.doc.sections, "Functions"):
        return
    if items := list(_iter_items(obj.functions)):
        name = "Methods" if isinstance(obj, Class) else "Functions"
        section = Section(name, Type(), Text(), items)
        obj.doc.sections.append(section)


def add_attributes(obj: Module | Class) -> None:
    """Add attributes section."""
    if get_by_type(obj.doc.sections, Attributes):
        return
    if get_by_name(obj.doc.sections, "Attributes"):
        return
    if items := list(_iter_items(obj.attributes)):
        section = Section("Attributes", Type(), Text(), items)
        obj.doc.sections.append(section)


ASNAME_PATTERN = re.compile(r"^\[.+?\]\[(__mkapi__\..+?)\]$")


def add_sections_for_package(module: Module) -> None:
    """Add __all__ members for a package."""
    modules = []
    classes = []
    functions = []
    attributes = []
    for name, fullname in get_all(module.name).items():
        if obj := get_object(fullname):
            item = _get_item(obj)
            asname = f"[{name}][\\1]"
            item.type.markdown = ASNAME_PATTERN.sub(asname, item.type.markdown)
            if isinstance(obj, Module):
                modules.append(item)
            elif isinstance(obj, Class):
                classes.append(item)
            elif isinstance(obj, Function):
                functions.append(item)
            elif isinstance(obj, Attribute):
                attributes.append(item)
    it = [
        (modules, "Modules"),
        (classes, "Classes"),
        (functions, "Functions"),
        (attributes, "Attributes"),
    ]
    for items, name in it:
        if get_by_name(module.doc.sections, name):
            continue
        if items:
            section = Section(name, Type(), Text(), items)
            module.doc.sections.append(section)


def _iter_items(objs: Iterable[Function | Class | Attribute]) -> Iterator[Item]:
    for obj in objs:
        if is_empty(obj):
            continue
        yield _get_item(obj)


def _get_item(obj: Module | Class | Function | Attribute) -> Item:
    type_ = obj.doc.type.copy()
    text = obj.doc.text.copy()
    type_.markdown = type_.markdown.split("..")[-1]
    text.markdown = text.markdown.split("\n\n")[0]
    return Item("", type_, text)
