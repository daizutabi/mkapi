"""AST module."""
from __future__ import annotations

import ast
import re
import typing
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
    Name,
    NodeTransformer,
    Raise,
)
from inspect import Parameter, cleandoc
from typing import TYPE_CHECKING

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Callable, Iterator
    from inspect import _ParameterKind

# type Import_ = Import | ImportFrom
# type Def = AsyncFunctionDef | FunctionDef | ClassDef
# type Assign_ = AnnAssign | Assign | TypeAlias
# type Node = Import_ | Def | Assign_

Import_: typing.TypeAlias = Import | ImportFrom
Def: typing.TypeAlias = AsyncFunctionDef | FunctionDef | ClassDef
Assign_: typing.TypeAlias = AnnAssign | Assign | TypeAlias  # type: ignore
Node: typing.TypeAlias = Import_ | Def | Assign_


def iter_child_nodes(node: AST) -> Iterator[Node]:
    """Yield child nodes."""
    yield_type = Import | ImportFrom | AsyncFunctionDef | FunctionDef | ClassDef
    for child in (it := ast.iter_child_nodes(node)):
        if isinstance(child, yield_type):
            yield child
        elif isinstance(child, AnnAssign | Assign | TypeAlias):
            yield from _iter_assign_nodes(child, it)
        else:
            yield from iter_child_nodes(child)


def _get_pseudo_docstring(node: AST) -> str | None:
    if isinstance(node, Expr) and isinstance(node.value, Constant):
        doc = node.value.value
        return cleandoc(doc) if isinstance(doc, str) else None
    return None


def _iter_assign_nodes(
    node: AnnAssign | Assign | TypeAlias,  # type: ignore
    it: Iterator[AST],
) -> Iterator[Node]:
    """Yield assign nodes."""
    node.__doc__ = None
    try:
        next_node = next(it)
    except StopIteration:
        yield node
        return
    if isinstance(next_node, AnnAssign | Assign | TypeAlias):
        yield node
        yield from _iter_assign_nodes(next_node, it)
    elif isinstance(next_node, AsyncFunctionDef | FunctionDef | ClassDef):
        yield node
        yield next_node
    else:
        node.__doc__ = _get_pseudo_docstring(next_node)
        yield node


def get_assign_name(node: AnnAssign | Assign | TypeAlias) -> str | None:  # type: ignore
    """Return the name of the assign node."""
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        return node.target.id
    if isinstance(node, Assign) and isinstance(node.targets[0], Name):
        return node.targets[0].id
    if TypeAlias and isinstance(node, TypeAlias) and isinstance(node.name, Name):
        return node.name.id
    return None


def get_assign_type(node: AnnAssign | Assign | TypeAlias) -> ast.expr | None:  # type: ignore
    """Return a type annotation of the Assign or TypeAlias AST node."""
    if isinstance(node, AnnAssign):
        return node.annotation
    if TypeAlias and isinstance(node, TypeAlias):
        return node.value
    return None


PARAMETER_KIND_ATTRIBUTE: dict[_ParameterKind, str] = {
    Parameter.POSITIONAL_ONLY: "posonlyargs",
    Parameter.POSITIONAL_OR_KEYWORD: "args",
    Parameter.VAR_POSITIONAL: "vararg",
    Parameter.KEYWORD_ONLY: "kwonlyargs",
    Parameter.VAR_KEYWORD: "kwarg",
}


def _iter_parameters(
    node: AsyncFunctionDef | FunctionDef,
) -> Iterator[tuple[ast.arg, _ParameterKind]]:
    for kind, attr in PARAMETER_KIND_ATTRIBUTE.items():
        if args := getattr(node.args, attr):
            it = args if isinstance(args, list) else [args]
            yield from ((arg, kind) for arg in it)


def _iter_defaults(node: AsyncFunctionDef | FunctionDef) -> Iterator[ast.expr | None]:
    args = node.args
    num_positional = len(args.posonlyargs) + len(args.args)
    nones = [None] * num_positional
    yield from [*nones, *args.defaults][-num_positional:]
    yield from args.kw_defaults


def iter_parameters(
    node: AsyncFunctionDef | FunctionDef,
) -> Iterator[tuple[ast.arg, _ParameterKind, ast.expr | None]]:
    """Yield parameters from a function node."""
    it = _iter_defaults(node)
    for arg, kind in _iter_parameters(node):
        default = None if kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD] else next(it)
        yield arg, kind, default


def iter_raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Raise]:
    """Yield [Raise] instances from a function node."""
    names = []
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and (type_ := child.exc):
            if isinstance(type_, ast.Call):
                type_ = type_.func
            if (name := ast.unparse(type_)) not in names:
                yield child
                names.append(name)


# a1.b_2(c[d]) -> a1, b_2, c, d
SPLIT_IDENTIFIER_PATTERN = re.compile(r"[\.\[\]\(\)|]|\s+")


def _split_name(name: str) -> list[str]:
    return [x for x in re.split(SPLIT_IDENTIFIER_PATTERN, name) if x]


def _is_identifier(name: str) -> bool:
    return name != "" and all(x.isidentifier() for x in _split_name(name))


def create_expr(name: str) -> ast.expr:
    """Return an [ast.expr] instance of a name."""
    if _is_identifier(name):
        try:
            expr = ast.parse(name).body[0]
        except SyntaxError:
            return ast.Constant("")
        if isinstance(expr, ast.Expr):
            return expr.value
    return ast.Constant(value=name)


PREFIX = "__mkapi__."


class Transformer(NodeTransformer):
    def _rename(self, name: str) -> Name:
        return Name(id=f"{PREFIX}{name}")

    def visit_Name(self, node: Name) -> Name:  # noqa: N802
        return self._rename(node.id)

    def unparse(self, node: ast.AST) -> str:
        node_ = ast.parse(ast.unparse(node))  # copy node for avoiding in-place rename.
        return ast.unparse(self.visit(node_))


class StringTransformer(Transformer):
    def visit_Constant(self, node: Constant) -> Constant | Name:  # noqa: N802
        if isinstance(node.value, str):
            return self._rename(node.value)
        return node


def _iter_identifiers(source: str) -> Iterator[tuple[str, bool]]:
    """Yield identifiers as a tuple of (code, isidentifier)."""
    start = 0
    while start < len(source):
        index = source.find(PREFIX, start)
        if index == -1:
            yield source[start:], False
            return
        if index != 0:
            yield source[start:index], False
        start = stop = index + len(PREFIX)
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


def _unparse(
    node: ast.AST,
    callback: Callable[[str], str],
    *,
    is_type: bool = True,
) -> Iterator[str]:
    trans = StringTransformer() if is_type else Transformer()
    source = trans.unparse(node)
    for code, isidentifier in _iter_identifiers(source):
        if isidentifier:
            yield callback(code)
        else:
            yield code


def unparse(
    node: ast.AST,
    callback: Callable[[str], str],
    *,
    is_type: bool = True,
) -> str:
    """Unparse the AST node with a callback function."""
    return "".join(_unparse(node, callback, is_type=is_type))


def is_property(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    read_only: bool = True,
) -> bool:
    """Return True if a function is a property."""
    for deco in node.decorator_list:
        deco_names = next(iter_identifiers(deco)).split(".")
        if len(deco_names) == 1 and deco_names[0] == "property":
            return True
        if read_only:
            continue
        if len(deco_names) == 2 and deco_names[1] == "setter":  # noqa: PLR2004
            return True
    return False


def has_overload(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if a function has an `overload` decorator."""
    for deco in node.decorator_list:
        deco_names = next(iter_identifiers(deco)).split(".")
        if len(deco_names) == 1 and deco_names[0] == "overload":
            return True
    return False


def is_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if a function is neither a property nor overloaded."""
    return not (is_property(node, read_only=False) or has_overload(node))
