"""importlib module."""
from __future__ import annotations

from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.docstrings
from mkapi.globals import get_all, get_fullname
from mkapi.inspect import is_dataclass, iter_dataclass_parameters
from mkapi.objects import (
    Attribute,
    Class,
    Function,
    Module,
    create_module,
    objects,
)
from mkapi.utils import cache, get_module_node_source, iter_parent_module_names

if TYPE_CHECKING:
    from collections.abc import Iterator


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


def _postprocess_class(cls: Class) -> None:
    for child in cls.classes:
        _postprocess_class(child)

    inherit_base_classes(cls)

    if is_dataclass(cls):
        cls.parameters = list(iter_dataclass_parameters(cls))


def iter_base_classes(cls: Class) -> Iterator[Class]:
    """Yield base classes."""
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
