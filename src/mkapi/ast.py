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
from typing import TYPE_CHECKING, Any, TypeAlias, TypeGuard

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


def iter_import_names(node: Module | Def) -> Iterator[tuple[str, str]]:
    """Yield imported names."""
    for child in iter_import_nodes(node):
        from_module = f"{child.module}." if isinstance(child, ImportFrom) else ""
        for alias in child.names:
            name = alias.asname or alias.name
            fullname = f"{from_module}{alias.name}"
            yield name, fullname


def get_import_names(node: Module | Def) -> dict[str, str]:
    """Return a dictionary of imported names as (name => fullname)."""
    return dict(iter_import_names(node))


def _is_assign_name(node: AST) -> TypeGuard[Assign_]:
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        return True
    if isinstance(node, Assign) and isinstance(node.targets[0], Name):
        return True
    return False


def _get_assign_name(node: AST) -> str | None:
    """Return the name of the assign node."""
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        return node.target.id
    if isinstance(node, Assign) and isinstance(node.targets[0], Name):
        return node.targets[0].id
    return None


def get_name(node: AST) -> str | None:
    """Return the node name."""
    if isinstance(node, Def):
        return node.name
    return _get_assign_name(node)


def get_by_name(nodes: Sequence[Def | Assign_], name: str) -> Def | Assign_ | None:
    """Return the node that has the name."""
    for node in nodes:
        if get_name(node) == name:
            return node
    return None


def iter_assign_nodes(node: Module | ClassDef) -> Iterator[Assign_]:
    """Yield assign nodes."""
    assign_node: Assign_ | None = None
    for child in ast.iter_child_nodes(node):
        if _is_assign_name(child):
            assign_node = child
        else:
            if assign_node:
                assign_node.__doc__ = _get_docstring(child)
                yield assign_node
            assign_node = None
    if assign_node:
        assign_node.__doc__ = None
        yield assign_node


def _get_docstring(node: AST) -> str | None:
    if not isinstance(node, Expr) or not isinstance(node.value, Constant):
        return None
    doc = node.value.value
    return cleandoc(doc) if isinstance(doc, str) else None


def get_assign_nodes(node: Module | ClassDef) -> list[Assign_]:
    """Return a list of assign nodes."""
    return list(iter_assign_nodes(node))


def iter_assign_names(node: Module | ClassDef) -> Iterator[tuple[str, str | None]]:
    """Yield assign node names."""
    for child in iter_assign_nodes(node):
        if name := _get_assign_name(child):
            fullname = child.value and ast.unparse(child.value)  # TODO @D: fix unparse
            yield name, fullname


def get_assign_names(node: Module | ClassDef) -> dict[str, str | None]:
    """Return a dictionary of assigned names as (name => fullname)."""
    return dict(iter_assign_names(node))


def iter_def_nodes(node: Module | ClassDef) -> Iterator[Def]:
    """Yield definition nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, Def):
            yield child


def get_def_nodes(node: Module | ClassDef) -> list[Def]:
    """Return a list of definition nodes."""
    return list(iter_def_nodes(node))


def iter_def_names(node: Module | ClassDef) -> Iterator[str]:
    """Yield definition node names."""
    for child in iter_def_nodes(node):
        yield child.name


def get_def_names(node: Module | ClassDef) -> list[str]:
    """Return a list of definition node names."""
    return list(iter_def_names(node))


def iter_names(node: Module | ClassDef) -> Iterator[tuple[str, str]]:
    """Yield import and def names."""
    yield from iter_import_names(node)
    for name in iter_def_names(node):
        yield name, f".{name}"
    for name, _ in iter_assign_names(node):
        yield name, f".{name}"


def get_names(node: Module | ClassDef) -> dict[str, str]:
    """Return a dictionary of import and def names."""
    return dict(iter_names(node))


def get_docstring(node: Doc) -> str | None:
    """Return the docstring for the given node or None if no docstring can be found."""
    if isinstance(node, Module | Def):
        return ast.get_docstring(node)
    if isinstance(node, Assign_):
        return node.__doc__
    msg = f"{node.__class__.__name__!r} can't have docstrings"
    raise TypeError(msg)


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
