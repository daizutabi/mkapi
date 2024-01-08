"""AST module."""
from __future__ import annotations

import ast
import importlib.util
from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    Module,
    Name,
    TypeAlias,
)
from inspect import Parameter, cleandoc
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Iterator
    from inspect import _ParameterKind


def iter_import_nodes(node: AST) -> Iterator[Import | ImportFrom]:
    """Yield import nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Import | ImportFrom):
            yield child
        elif not isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield from iter_import_nodes(child)


def _get_pseudo_docstring(node: AST) -> str | None:
    if not isinstance(node, Expr) or not isinstance(node.value, Constant):
        return None
    doc = node.value.value
    return cleandoc(doc) if isinstance(doc, str) else None


def iter_assign_nodes(
    node: Module | ClassDef,
) -> Iterator[AnnAssign | Assign | TypeAlias]:
    """Yield assign nodes."""
    assign_node: AnnAssign | Assign | TypeAlias | None = None
    for child in ast.iter_child_nodes(node):
        if isinstance(child, AnnAssign | Assign | TypeAlias):
            if assign_node:
                yield assign_node
            child.__doc__ = None
            assign_node = child
        else:
            if assign_node:
                assign_node.__doc__ = _get_pseudo_docstring(child)
                yield assign_node
            assign_node = None
    if assign_node:
        assign_node.__doc__ = None
        yield assign_node


def get_assign_name(node: AnnAssign | Assign | TypeAlias) -> str | None:
    """Return the name of the assign node."""
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        return node.target.id
    if isinstance(node, Assign) and isinstance(node.targets[0], Name):
        return node.targets[0].id
    if isinstance(node, TypeAlias) and isinstance(node.name, Name):
        return node.name.id
    return None


def get_assign_type(node: AnnAssign | Assign | TypeAlias) -> ast.expr | None:
    """Return a type annotation of the Assign or TypeAlias AST node."""
    if isinstance(node, AnnAssign):
        return node.annotation
    if isinstance(node, TypeAlias):
        return node.value
    return None


PARAMETER_KIND_DICT: dict[_ParameterKind, str] = {
    Parameter.POSITIONAL_ONLY: "posonlyargs",  # before '/', list
    Parameter.POSITIONAL_OR_KEYWORD: "args",  # normal, list
    Parameter.VAR_POSITIONAL: "vararg",  # *args, arg or None
    Parameter.KEYWORD_ONLY: "kwonlyargs",  # after '*' or '*args', list
    Parameter.VAR_KEYWORD: "kwarg",  # **kwargs, arg or None
}


def _iter_parameters(
    node: FunctionDef | AsyncFunctionDef,
) -> Iterator[tuple[ast.arg, _ParameterKind]]:
    for kind, attr in PARAMETER_KIND_DICT.items():
        if args := getattr(node.args, attr):
            it = args if isinstance(args, list) else [args]
            yield from ((arg, kind) for arg in it)


def _iter_defaults(node: FunctionDef | AsyncFunctionDef) -> Iterator[ast.expr | None]:
    args = node.args
    num_positional = len(args.posonlyargs) + len(args.args)
    nones = [None] * num_positional
    yield from [*nones, *args.defaults][-num_positional:]
    yield from args.kw_defaults


def iter_parameters(
    node: FunctionDef | AsyncFunctionDef,
) -> Iterator[tuple[ast.arg, _ParameterKind, ast.expr | None]]:
    """Yield parameters from the function node."""
    it = _iter_defaults(node)
    for arg, kind in _iter_parameters(node):
        if kind is Parameter.VAR_POSITIONAL:
            arg.arg, default = f"*{arg.arg}", None
        elif kind is Parameter.VAR_KEYWORD:
            arg.arg, default = f"**{arg.arg}", None
        else:
            default = next(it)
        yield arg, kind, default


def iter_callable_nodes(
    node: Module | ClassDef,
) -> Iterator[FunctionDef | AsyncFunctionDef | ClassDef]:
    """Yield callable nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield child
