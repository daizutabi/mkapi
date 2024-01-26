"""importlib module."""
from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.docstrings
from mkapi.globals import get_fullname
from mkapi.inspect import is_dataclass, iter_dataclass_parameters
from mkapi.objects import Class, Module, create_module, objects
from mkapi.utils import (
    del_by_name,
    get_by_name,
    get_module_node_source,
    iter_parent_module_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.objects import Attribute, Function


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
            return "\n".join(obj.source.split("\n")[:maxline])
        return None
    if (module := obj.module) and (source := module.source):
        start, stop = obj.node.lineno - 1, obj.node.end_lineno
        return "\n".join(source.split("\n")[start:stop][:maxline])
    return None


def _postprocess(obj: Module | Class) -> None:
    if isinstance(obj, Class):
        _postprocess_class(obj)
    for cls in obj.classes:
        _postprocess(cls)


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
