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
)
from dataclasses import dataclass
from inspect import Parameter, cleandoc
from typing import TYPE_CHECKING, TypeAlias, TypeGuard

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Iterator, Sequence
    from inspect import _ParameterKind

Import_: TypeAlias = Import | ImportFrom
FuncDef: TypeAlias = AsyncFunctionDef | FunctionDef
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


def iter_nodes(node: Module | ClassDef) -> Iterator[Def | Assign_]:
    """Yield nodes."""
    yield from iter_assign_nodes(node)
    yield from iter_def_nodes(node)


def get_nodes(node: Module | ClassDef) -> list[Def | Assign_]:
    """Return a list of nodes."""
    return list(iter_nodes(node))


def iter_names(node: Module | ClassDef) -> Iterator[tuple[str, str]]:
    """Yield names as (name, fullname) pairs."""
    yield from iter_import_names(node)
    for name, _ in iter_assign_names(node):
        yield name, f".{name}"
    for name in iter_def_names(node):
        yield name, f".{name}"


def get_names(node: Module | ClassDef) -> dict[str, str]:
    """Return a dictionary of names as (name => fullname)."""
    return dict(iter_names(node))


def get_docstring(node: Doc) -> str | None:
    """Return the docstring for the given node or None if no docstring can be found."""
    if isinstance(node, Module | Def):
        return ast.get_docstring(node)
    if isinstance(node, Assign_):
        return node.__doc__
    msg = f"{node.__class__.__name__!r} can't have docstrings"
    raise TypeError(msg)


ARGS_KIND: dict[_ParameterKind, str] = {
    Parameter.POSITIONAL_ONLY: "posonlyargs",  # before '/', list
    Parameter.POSITIONAL_OR_KEYWORD: "args",  # normal, list
    Parameter.VAR_POSITIONAL: "vararg",  # *args, arg or None
    Parameter.KEYWORD_ONLY: "kwonlyargs",  # after '*' or '*args', list
    Parameter.VAR_KEYWORD: "kwarg",  # **kwargs, arg or None
}


def iter_arguments(node: FuncDef) -> Iterator[tuple[ast.arg, _ParameterKind]]:
    """Yield arguments from the function node."""
    for kind, attr in ARGS_KIND.items():
        if args := getattr(node.args, attr):
            it = args if isinstance(args, list) else [args]
            yield from ((arg, kind) for arg in it)


def iter_defaults(node: FuncDef) -> Iterator[ast.expr | None]:
    """Yield defaults from the function node."""
    args = node.args
    num_positional = len(args.posonlyargs) + len(args.args)
    nones = [None] * num_positional
    yield from [*nones, *args.defaults][-num_positional:]
    yield from args.kw_defaults


@dataclass
class _Argument:
    annotation: ast.expr | None
    default: ast.expr | None
    kind: _ParameterKind


@dataclass
class _Arguments:
    _args: dict[str, _Argument]

    def __getattr__(self, name: str) -> _Argument:
        return self._args[name]


def get_arguments(node: FuncDef) -> _Arguments:
    """Return a dictionary of the function arguments."""
    it = iter_defaults(node)
    args: dict[str, _Argument] = {}
    for arg, kind in iter_arguments(node):
        if kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]:
            default = None
        else:
            default = next(it)
        args[arg.arg] = _Argument(arg.annotation, default, kind)
    return _Arguments(args)
