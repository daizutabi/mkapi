"""importlib module."""
from __future__ import annotations

from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.globals import get_fullname

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator

    from mkapi.objects import Class, Function


def iter_decorator_names(obj: Class | Function) -> Iterator[str]:
    """Yield decorator_names."""
    for deco in obj.node.decorator_list:
        deco_name = next(mkapi.ast.iter_identifiers(deco))

        if name := get_fullname(deco_name, obj.module.name.str):
            yield name

        else:
            yield deco_name


def get_decorator(obj: Class | Function, name: str) -> ast.expr | None:
    """Return a decorator expr by name."""
    for deco in obj.node.decorator_list:
        deco_name = next(mkapi.ast.iter_identifiers(deco))

        if get_fullname(deco_name, obj.module.name.str) == name:
            return deco

        if deco_name == name:
            return deco

    return None


def is_dataclass(cls: Class) -> bool:
    """Return True if the [Class] instance is a dataclass."""
    return get_decorator(cls, "dataclasses.dataclass") is not None


def is_classmethod(func: Function) -> bool:
    """Return True if the [Function] instance is a classmethod."""
    return get_decorator(func, "classmethod") is not None


def is_staticmethod(func: Function) -> bool:
    """Return True if the [Function] instance is a staticmethod."""
    return get_decorator(func, "staticmethod") is not None


# def _iter_decorator_args(deco: ast.expr) -> Iterator[tuple[str, Any]]:
#     for child in ast.iter_child_nodes(deco):
#         if isinstance(child, ast.keyword):
#             if child.arg and isinstance(child.value, ast.Constant):
#                 yield child.arg, child.value.value


# def _get_decorator_args(deco: ast.expr) -> dict[str, Any]:
#     return dict(_iter_decorator_args(deco))
