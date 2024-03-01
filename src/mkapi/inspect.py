"""Object module."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import mkapi.nodes
from mkapi.nodes import parse, resolve_from_module
from mkapi.objects import Module, Object, Parent, create_module, objects
from mkapi.utils import (
    cache,
    get_module_node,
    get_module_node_source,
    get_module_source,
    iter_attribute_names,
    split_name,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def get_source(obj: Object) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        return get_module_source(obj.name)

    if source := get_module_source(obj.module):
        return ast.get_source_segment(source, obj.node)

    return None


def is_child(obj: Object, parent: Object | None) -> bool:
    """Return True if obj is a member of parent."""
    if parent is None or isinstance(obj, Module) or isinstance(parent, Module):
        return True

    return obj.parent is parent


@cache
def get_object(fullname: str) -> Object | None:
    if obj := objects.get(fullname):
        return obj

    for module in iter_attribute_names(fullname):
        if create_module(module) and (obj := objects.get(fullname)):
            return obj

    return None


@cache
def resolve(fullname: str) -> tuple[str, str | None, Object] | None:
    if obj := create_module(fullname):
        return fullname, None, obj

    if "." not in fullname:
        return None

    module, name = fullname.rsplit(".", maxsplit=1)

    if (obj := create_module(module)) and (child := obj.get(name)):
        return name, module, child

    if "." not in module:
        return None

    module, name, attr = fullname.rsplit(".", maxsplit=2)

    if obj := create_module(module):  # noqa: SIM102
        if (child := obj.get(name)) and isinstance(child, Parent):  # noqa: SIM102
            if child := child.get(attr):
                return f"{name}.{attr}", module, child

    return None


def resolve_from_object(name: str, obj: Object) -> str | None:
    """Return fullname from object."""
    if isinstance(obj, Module):
        return resolve_from_module(name, obj.name)

    if isinstance(obj, Parent):  # noqa: SIM102
        if child := obj.get(name):
            return child.fullname

    if "." not in name:
        if obj.parent:
            return resolve_from_object(name, obj.parent)

        return resolve_from_module(name, obj.module)

    parent, name_ = name.rsplit(".", maxsplit=1)

    if obj_ := objects.get(parent):
        return resolve_from_object(name, obj_)

    if obj.name == parent:
        return resolve_from_object(name_, obj)

    if resolved := resolve(name):
        return resolved[2].fullname

    return None


# def iter_child_objects(
#     obj: Parent,
#     predicate: Callable_[[Object, Object | None], bool] | None = None,
# ) -> Iterator[tuple[str, Object]]:
#     """Yield child [Object] instances."""
#     for name, child in obj.children.items():
#         if not predicate or predicate(child, obj):
#             yield name, child
#             if isinstance(child,Pa)
#             yield from iter_objects_with_depth(child, maxdepth, predicate, depth + 1)


# def iter_objects(
#     obj: Object,
#     maxdepth: int = -1,
#     predicate: Callable_[[Object, Object | None], bool] | None = None,
# ) -> Iterator[Object]:
#     """Yield [Object] instances."""
#     for child, _ in iter_objects_with_depth(obj, maxdepth, predicate, 0):
#         yield child
