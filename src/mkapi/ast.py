"""AST module."""
from __future__ import annotations

import ast
import re
from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Call,
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
from dataclasses import dataclass
from inspect import Parameter as P  # noqa: N817
from inspect import cleandoc
from typing import TYPE_CHECKING

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Callable, Iterator
    from inspect import _ParameterKind


def iter_child_nodes(node: AST) -> Iterator[AST]:
    """Yield child nodes."""
    it = ast.iter_child_nodes(node)

    for child in it:
        if isinstance(child, Import | ImportFrom | ClassDef | FunctionDef | AsyncFunctionDef):
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
) -> Iterator[AST]:
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

    elif isinstance(next_node, FunctionDef | AsyncFunctionDef | ClassDef):
        yield node
        yield next_node

    else:
        node.__doc__ = _get_pseudo_docstring(next_node)
        yield node


def get_assign_name(node: AnnAssign | Assign | TypeAlias) -> str | None:  # type: ignore
    """Return the name of the assign node."""
    if isinstance(node, Assign):
        target = node.targets[0]

    elif isinstance(node, AnnAssign):
        target = node.target

    elif TypeAlias and isinstance(node, TypeAlias):
        target = node.name

    else:
        return None

    if isinstance(target, Name | Attribute):
        return ast.unparse(target)

    return None


def get_assign_type(node: AnnAssign | Assign | TypeAlias) -> ast.expr | None:  # type: ignore
    """Return a type annotation of the Assign or TypeAlias AST node."""
    if isinstance(node, AnnAssign):
        return node.annotation

    if TypeAlias and isinstance(node, TypeAlias):
        return node.value

    return None


def _iter_parameters(
    node: FunctionDef | AsyncFunctionDef,
) -> Iterator[tuple[str, ast.expr | None, _ParameterKind]]:
    args = node.args
    for arg in args.posonlyargs:
        yield arg.arg, arg.annotation, P.POSITIONAL_ONLY
    for arg in args.args:
        yield arg.arg, arg.annotation, P.POSITIONAL_OR_KEYWORD
    if arg := args.vararg:
        yield arg.arg, arg.annotation, P.VAR_POSITIONAL
    for arg in args.kwonlyargs:
        yield arg.arg, arg.annotation, P.KEYWORD_ONLY
    if arg := args.kwarg:
        yield arg.arg, arg.annotation, P.VAR_KEYWORD


def _iter_defaults(node: FunctionDef | AsyncFunctionDef) -> Iterator[ast.expr | None]:
    args = node.args
    num_positional = len(args.posonlyargs) + len(args.args)
    nones = [None] * num_positional

    yield from [*nones, *args.defaults][-num_positional:]
    yield from args.kw_defaults


@dataclass
class Parameter:
    name: str
    type: ast.expr | None
    default: ast.expr | None
    kind: _ParameterKind

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


def iter_parameters(node: FunctionDef | AsyncFunctionDef) -> Iterator[Parameter]:
    """Yield parameters from a function node."""
    it = _iter_defaults(node)
    for name, type_, kind in _iter_parameters(node):
        default = None if kind in [P.VAR_POSITIONAL, P.VAR_KEYWORD] else next(it)
        yield Parameter(name, type_, default, kind)


def iter_raises(node: FunctionDef | AsyncFunctionDef) -> Iterator[ast.expr]:
    """Yield unique raises from a function node."""
    names = []
    for child in ast.walk(node):
        if isinstance(child, Raise) and (type_ := child.exc):
            if isinstance(type_, Call):
                type_ = type_.func

            name = ast.unparse(type_)
            if name not in names:
                yield type_
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
            return Constant("")

        if isinstance(expr, Expr):
            return expr.value

    return Constant(value=name)


PREFIX = "__mkapi__."


class Transformer(NodeTransformer):
    def _rename(self, name: str) -> Name:
        return Name(id=f"{PREFIX}{name}")

    def visit_Name(self, node: Name) -> Name:  # noqa: N802
        return self._rename(node.id)

    def unparse(self, node: AST) -> str:
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


def iter_identifiers(node: AST) -> Iterator[str]:
    """Yield identifiers."""
    source = StringTransformer().unparse(node)
    for code, isidentifier in _iter_identifiers(source):
        if isidentifier:
            yield code


def _unparse(node: AST, callback: Callable[[str], str], *, is_type: bool = True) -> Iterator[str]:
    trans = StringTransformer() if is_type else Transformer()
    source = trans.unparse(node)
    for code, isidentifier in _iter_identifiers(source):
        if isidentifier:
            yield callback(code)

        else:
            yield code


def unparse(node: AST, callback: Callable[[str], str], *, is_type: bool = True) -> str:
    """Unparse the AST node with a callback function."""
    return "".join(_unparse(node, callback, is_type=is_type))


def has_property(node: AST, name: str, index: int = 0) -> bool:
    if not isinstance(node, FunctionDef | AsyncFunctionDef):
        return False

    for deco in node.decorator_list:
        deco_names = next(iter_identifiers(deco)).split(".")

        if len(deco_names) == index + 1 and deco_names[index] == name:
            return True

    return False


def is_property(node: AST) -> bool:
    """Return True if a function is a property."""
    return has_property(node, "property")


def is_setter(node: AST) -> bool:
    """Return True if a function is a property."""
    return has_property(node, "setter", 1)


def has_overload(node: AST) -> bool:
    """Return True if a function has an `overload` decorator."""
    return has_property(node, "overload")


def is_function(node: AST) -> bool:
    """Return True if a function is neither a property nor overloaded."""
    return not (is_property(node) or is_setter(node) or has_overload(node))


def is_classmethod(node: AST) -> bool:
    return has_property(node, "classmethod")


def is_staticmethod(node: AST) -> bool:
    return has_property(node, "staticmethod")
