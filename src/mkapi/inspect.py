"""importlib module."""
from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.ast import PARAMETER_KIND_ATTRIBUTE
from mkapi.globals import get_fullname
from mkapi.items import Parameter
from mkapi.objects import Class
from mkapi.utils import get_by_name

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator

    from mkapi.objects import Function


def get_decorator(obj: Class | Function, name: str) -> ast.expr | None:
    """Return a decorator expr by name."""
    if not obj.module:
        return None
    for deco in obj.node.decorator_list:
        deco_name = next(mkapi.ast.iter_identifiers(deco))
        if get_fullname(obj.module.name, deco_name) == name:
            return deco
    return None


def is_dataclass(cls: Class) -> bool:
    """Return True if a [Class] instance is a dataclass."""
    return get_decorator(cls, "dataclasses.dataclass") is not None


# def _iter_decorator_args(deco: ast.expr) -> Iterator[tuple[str, Any]]:
#     for child in ast.iter_child_nodes(deco):
#         if isinstance(child, ast.keyword):
#             if child.arg and isinstance(child.value, ast.Constant):
#                 yield child.arg, child.value.value


# def _get_decorator_args(deco: ast.expr) -> dict[str, Any]:
#     return dict(_iter_decorator_args(deco))


def iter_dataclass_parameters(cls: Class) -> Iterator[Parameter]:
    """Yield [Parameter] instances a for dataclass signature."""
    if not cls.module or not (module_name := cls.module.name):
        raise NotImplementedError
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return
    members = dict(inspect.getmembers(module, inspect.isclass))
    obj = members[cls.name]

    for param in inspect.signature(obj).parameters.values():
        if attr := get_by_name(cls.attributes, param.name):
            args = (attr.name, attr.type, attr.doc.text, attr.default)
            yield Parameter(*args, param.kind)
        else:
            raise NotImplementedError


@dataclass
class Part:
    """Signature part."""

    text: str
    kind: str


@dataclass
class Signature:
    """Signature."""

    parts: list[Part]

    def __iter__(self) -> Iterator[Part]:
        return iter(self.parts)


def _iter_sep(kind: str | None, prev_kind: str | None) -> Iterator[tuple[str, str]]:
    if prev_kind == "posonlyargs" and kind != prev_kind:
        yield "/", "sep"
        yield ", ", "comma"
    if kind == "kwonlyargs" and prev_kind not in [kind, "vararg"]:
        yield "*", "sep"
        yield ", ", "comma"
    if kind == "vararg":
        yield "*", "star"
    if kind == "kwarg":
        yield "**", "star"


def _iter_param(param: Parameter, kind: str) -> Iterator[tuple[str, str]]:
    yield param.name, kind
    if param.type.expr:
        yield ":", "colon"
        yield param.type.html, "ann"
    if param.default.expr:
        yield "=", "eq"
        yield param.default.html, "default"


def iter_signature(obj: Class | Function) -> Iterator[tuple[str, str]]:
    """Yield signature."""
    yield "(", "paren"
    n = len(obj.parameters)
    prev_kind = kind = None
    for k, param in enumerate(obj.parameters):
        kind = PARAMETER_KIND_ATTRIBUTE[param.kind]
        yield from _iter_sep(kind, prev_kind)
        yield from _iter_param(param, kind)
        if k < n - 1:
            yield ", ", "comma"
        prev_kind = kind
    if kind == "posonlyargs":
        yield ", ", "comma"
        yield "/", "sep"
    yield ")", "paren"
    if isinstance(obj, Class) or not obj.returns:
        return
    yield "→", "arrow"
    yield obj.returns[0].type.html, "return"


def get_signature(obj: Class | Function) -> Signature:
    """Return signature."""
    parts = [Part(*args) for args in iter_signature(obj)]
    return Signature(parts)


# Parameter.POSITIONAL_ONLY: "posonlyargs",
# Parameter.POSITIONAL_OR_KEYWORD: "args",
# Parameter.VAR_POSITIONAL: "vararg",
# Parameter.KEYWORD_ONLY: "kwonlyargs",
# Parameter.VAR_KEYWORD: "kwarg",
