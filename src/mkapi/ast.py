"""AST module."""
from __future__ import annotations

import ast
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
    NodeTransformer,
    TypeAlias,
)
from inspect import Parameter, cleandoc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Callable, Iterator
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
    Parameter.POSITIONAL_ONLY: "posonlyargs",
    Parameter.POSITIONAL_OR_KEYWORD: "args",
    Parameter.VAR_POSITIONAL: "vararg",
    Parameter.KEYWORD_ONLY: "kwonlyargs",
    Parameter.VAR_KEYWORD: "kwarg",
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


class Transformer(NodeTransformer):  # noqa: D101
    def _rename(self, name: str) -> Name:
        return Name(id=f"__mkapi__.{name}")

    def visit_Name(self, node: Name) -> Name:  # noqa: N802, D102
        return self._rename(node.id)

    def unparse(self, node: ast.AST) -> str:  # noqa: D102
        node_ = ast.parse(ast.unparse(node))  # copy node for avoiding in-place rename.
        return ast.unparse(self.visit(node_))


class StringTransformer(Transformer):  # noqa: D101
    def visit_Constant(self, node: Constant) -> Constant | Name:  # noqa: N802, D102
        if isinstance(node.value, str):
            return self._rename(node.value)
        return node


def _iter_identifiers(source: str) -> Iterator[tuple[str, bool]]:
    """Yield identifiers as a tuple of (code, isidentifier)."""
    start = 0
    while start < len(source):
        index = source.find("__mkapi__.", start)
        if index == -1:
            yield source[start:], False
            return
        if index != 0:
            yield source[start:index], False
        start = stop = index + 10  # 10 == len("__mkapi__.")
        while stop < len(source):
            c = source[stop]
            if c == "." or c.isdigit() or c.isidentifier():
                stop += 1
            else:
                break
        yield source[start:stop], True
        start = stop


def iter_identifiers(node: ast.AST) -> Iterator[str]:
    """Yield identifiers."""
    source = StringTransformer().unparse(node)
    for code, isidentifier in _iter_identifiers(source):
        if isidentifier:
            yield code


def _unparse(node: ast.AST, callback: Callable[[str], str]) -> Iterator[str]:
    source = StringTransformer().unparse(node)
    for code, isidentifier in _iter_identifiers(source):
        if isidentifier:
            yield callback(code)
        else:
            yield code


def unparse(node: ast.AST, callback: Callable[[str], str]) -> str:
    """Unparse the AST node with a callback function."""
    return "".join(_unparse(node, callback))