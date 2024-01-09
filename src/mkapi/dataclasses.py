"""Dataclass function."""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any

from mkapi.ast import iter_identifiers

if TYPE_CHECKING:
    from mkapi.objects import Class, Iterator, Module


def _get_dataclass_decorator(cls: Class, module: Module) -> ast.expr | None:
    for deco in cls._node.decorator_list:
        name = next(iter_identifiers(deco))
        if module.get_fullname(name) == "dataclasses.dataclass":
            return deco
    return None


def is_dataclass(cls: Class, module: Module) -> bool:
    """Return True if the class is a dataclass."""
    return _get_dataclass_decorator(cls, module) is not None


def _iter_decorator_args(deco: ast.expr) -> Iterator[tuple[str, Any]]:
    for child in ast.iter_child_nodes(deco):
        if isinstance(child, ast.keyword):  # noqa: SIM102
            if child.arg and isinstance(child.value, ast.Constant):
                yield child.arg, child.value.value


def _get_decorator_args(deco: ast.expr) -> dict[str, Any]:
    return dict(_iter_decorator_args(deco))
