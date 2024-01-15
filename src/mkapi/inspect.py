"""Inspect module."""
from __future__ import annotations

from typing import TYPE_CHECKING

from mkapi.objects import Class, Function, Module
from mkapi.utils import get_by_name

if TYPE_CHECKING:
    from mkapi.items import Attribute, Import, Parameter, Raise

type Object = Module | Class | Function


def get_source(obj: Object, maxline: int | None = None) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        if obj.source:
            return "\n".join(obj.source.split("\n")[:maxline])
        return None
    if (module := obj.module) and (source := module.source):
        start, stop = obj.node.lineno - 1, obj.node.end_lineno
        return "\n".join(source.split("\n")[start:stop][:maxline])
    return None


def get_class(obj: Object, name: str) -> Class | None:
    """Return a [Class] instance by the name."""
    return get_by_name(obj.classes, name)


def get_function(obj: Object, name: str) -> Function | None:
    """Return a [Function] instance by the name."""
    return get_by_name(obj.functions, name)


def get_attribute(obj: Module | Class, name: str) -> Attribute | None:
    """Return an [Attribute] instance by the name."""
    return get_by_name(obj.attributes, name)


def get_parameter(obj: Class | Function, name: str) -> Parameter | None:
    """Return a [Parameter] instance by the name."""
    return get_by_name(obj.parameters, name)


def get_raise(obj: Class | Function, name: str) -> Raise | None:
    """Return a [Raise] instance by the name."""
    return get_by_name(obj.raises, name)


def get_import(obj: Module, name: str) -> Import | None:
    """Return an [Import] instance by the name."""
    return get_by_name(obj.imports, name)
