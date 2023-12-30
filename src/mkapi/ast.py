"""AST module."""
from __future__ import annotations

import ast
from ast import (
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    List,
    Module,
    Name,
    Subscript,
    Tuple,
)
from inspect import cleandoc
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Callable, Iterator, Sequence

Import_: TypeAlias = Import | ImportFrom
Def: TypeAlias = AsyncFunctionDef | FunctionDef | ClassDef
Assign_: TypeAlias = Assign | AnnAssign
Doc: TypeAlias = Module | Def | Assign_


def iter_import_nodes(node: AST) -> Iterator[Import_]:
    """Yield import nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, Import_):
            yield child
        elif not isinstance(child, Def):
            yield from iter_import_nodes(child)


def iter_import_names(node: AST) -> Iterator[tuple[str | None, str, str | None]]:
    """Yield imported names."""
    for child in iter_import_nodes(node):
        from_module = None if isinstance(child, Import) else child.module
        for alias in child.names:
            yield from_module, alias.name, alias.asname


def get_import_names(node: AST) -> list[tuple[str | None, str, str | None]]:
    """Return a list of imported names."""
    return list(iter_import_names(node))


def iter_def_nodes(node: AST) -> Iterator[Def]:
    """Yield definition nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, Def):
            yield child


def get_def_nodes(node: AST) -> list[Def]:
    """Return a list of definition nodes."""
    return list(iter_def_nodes(node))


def _get_docstring(node: AST) -> str | None:
    if not isinstance(node, Expr) or not isinstance(node.value, Constant):
        return None
    doc = node.value.value
    return cleandoc(doc) if isinstance(doc, str) else None


def iter_assign_nodes(node: AST) -> Iterator[Assign_]:
    """Yield assign nodes."""
    assign_node: Assign_ | None = None
    for child in ast.iter_child_nodes(node):
        if isinstance(child, Assign_):
            assign_node = child
        else:
            if assign_node:
                assign_node.__doc__ = _get_docstring(child)
                yield assign_node
            assign_node = None
    if assign_node:
        assign_node.__doc__ = None
        yield assign_node


def get_assign_nodes(node: AST) -> list[Assign_]:
    """Return a list of assign nodes."""
    return list(iter_assign_nodes(node))


def get_docstring(node: Doc) -> str | None:
    """Return the docstring for the given node or None if no docstring can be found."""
    if isinstance(node, Module | Def):
        return ast.get_docstring(node)
    if isinstance(node, Assign_):
        return node.__doc__
    msg = f"{node.__class__.__name__!r} can't have docstrings"
    raise TypeError(msg)


def get_name(node: AST) -> str | None:
    """Return the node name."""
    if isinstance(node, Def):
        return node.name
    if isinstance(node, Assign):
        for target in node.targets:
            if isinstance(target, Name):
                return target.id
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        return node.target.id
    return None


def get_by_name(nodes: Sequence[Def | Assign_], name: str) -> Def | Assign_ | None:
    """Return the node that has the name."""
    for node in nodes:
        if get_name(node) == name:
            return node
    return None


def parse_attribute(node: Attribute) -> str:  # noqa: D103
    return ".".join([parse_node(node.value), node.attr])


def parse_subscript(node: Subscript) -> str:  # noqa: D103
    value = parse_node(node.value)
    slice_ = parse_node(node.slice)
    return f"{value}[{slice_}]"


def parse_constant(node: Constant) -> str:  # noqa: D103
    if node.value is Ellipsis:
        return "..."
    if isinstance(node.value, str):
        return node.value
    return parse_value(node.value)


def parse_list(node: List) -> str:  # noqa: D103
    return "[" + ", ".join(parse_node(n) for n in node.elts) + "]"


def parse_tuple(node: Tuple) -> str:  # noqa: D103
    return ", ".join(parse_node(n) for n in node.elts)


def parse_value(value: Any) -> str:  # noqa: D103, ANN401
    return str(value)


PARSE_NODE_FUNCTIONS: list[tuple[type, Callable[..., str] | str]] = [
    (Attribute, parse_attribute),
    (Subscript, parse_subscript),
    (Constant, parse_constant),
    (List, parse_list),
    (Tuple, parse_tuple),
    (Name, "id"),
]


def parse_node(node: AST) -> str:
    """Return the string expression for an AST node."""
    for type_, parse in PARSE_NODE_FUNCTIONS:
        if isinstance(node, type_):
            node_str = parse(node) if callable(parse) else getattr(node, parse)
            return node_str if isinstance(node_str, str) else str(node_str)
    return ast.unparse(node)
