"""Dataclass function."""
from __future__ import annotations

import ast
import importlib
import inspect
from typing import TYPE_CHECKING

from mkapi.ast import iter_identifiers

if TYPE_CHECKING:
    from inspect import _ParameterKind

    from mkapi.objects import Any, Attribute, Class, Iterator, Module


def _get_dataclass_decorator(cls: Class, module: Module) -> ast.expr | None:
    for deco in cls._node.decorator_list:
        name = next(iter_identifiers(deco))
        if module.get_fullname(name) == "dataclasses.dataclass":
            return deco
    return None


def is_dataclass(cls: Class, module: Module | None = None) -> bool:
    """Return True if the class is a dataclass."""
    if module := module or cls.get_module():
        return _get_dataclass_decorator(cls, module) is not None
    return False


def iter_parameters(cls: Class) -> Iterator[tuple[Attribute, _ParameterKind]]:
    """Yield tuples of ([Attribute], [_ParameterKind]) for dataclass signature."""
    attrs: dict[str, Attribute] = {}
    for base in cls.iter_bases():
        if not is_dataclass(base):
            raise NotImplementedError
        for attr in base.attributes:
            attrs[attr.name] = attr  # updated by subclasses.

    if not (modulename := cls.modulename):
        raise NotImplementedError
    module = importlib.import_module(modulename)
    members = dict(inspect.getmembers(module, inspect.isclass))
    obj = members[cls.name]

    for param in inspect.signature(obj).parameters.values():
        if param.name not in attrs:
            raise NotImplementedError
        yield attrs[param.name], param.kind


# --------------------------------------------------------------


def _iter_decorator_args(deco: ast.expr) -> Iterator[tuple[str, Any]]:
    for child in ast.iter_child_nodes(deco):
        if isinstance(child, ast.keyword):  # noqa: SIM102
            if child.arg and isinstance(child.value, ast.Constant):
                yield child.arg, child.value.value


def _get_decorator_args(deco: ast.expr) -> dict[str, Any]:
    return dict(_iter_decorator_args(deco))
