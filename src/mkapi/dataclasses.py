"""Dataclass function."""
from __future__ import annotations

import ast
import importlib
import inspect
from typing import TYPE_CHECKING

from mkapi.ast import iter_identifiers

if TYPE_CHECKING:
    from inspect import _ParameterKind
    from typing import Any

    from mkapi.objects import Attribute, Class, Iterator, Module


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
    if not (modulename := cls.modulename):
        raise NotImplementedError
    try:
        module = importlib.import_module(modulename)
    except ModuleNotFoundError:
        return
    members = dict(inspect.getmembers(module, inspect.isclass))
    obj = members[cls.name]

    for param in inspect.signature(obj).parameters.values():
        if attr := cls.get_attribute(param.name):
            yield attr, param.kind


# --------------------------------------------------------------


def _iter_decorator_args(deco: ast.expr) -> Iterator[tuple[str, Any]]:
    for child in ast.iter_child_nodes(deco):
        if isinstance(child, ast.keyword):  # noqa: SIM102
            if child.arg and isinstance(child.value, ast.Constant):
                yield child.arg, child.value.value


def _get_decorator_args(deco: ast.expr) -> dict[str, Any]:
    return dict(_iter_decorator_args(deco))
