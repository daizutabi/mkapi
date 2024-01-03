"""AST module."""
from __future__ import annotations

import ast
from ast import (
    AnnAssign,
    AsyncFunctionDef,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    ImportFrom,
    Name,
    TypeAlias,
)
from dataclasses import dataclass
from importlib.util import find_spec
from inspect import Parameter as P  # noqa: N817
from inspect import cleandoc
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Iterator
    from inspect import _ParameterKind

type FunctionDef_ = AsyncFunctionDef | FunctionDef
type Def = FunctionDef_ | ClassDef
type Assign_ = ast.Assign | AnnAssign | TypeAlias
type Doc = ast.Module | Def | Assign_

module_cache: dict[str, tuple[float, ast.Module]] = {}


def get_module_node(name: str) -> ast.Module:
    """Return a [ast.Module] node by name."""
    spec = find_spec(name)
    if not spec or not spec.origin:
        raise ModuleNotFoundError
    path = Path(spec.origin)
    mtime = path.stat().st_mtime
    if name in module_cache and mtime == module_cache[name][0]:
        return module_cache[name][1]
    if not path.exists():
        raise ModuleNotFoundError
    with path.open(encoding="utf-8") as f:
        source = f.read()
    node = ast.parse(source)
    module_cache[name] = (mtime, node)
    return node


def iter_import_nodes(node: AST) -> Iterator[ast.Import | ImportFrom]:
    """Yield import nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Import | ImportFrom):
            yield child
        elif not isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield from iter_import_nodes(child)


def iter_import_node_names(
    node: ast.Module | Def,
) -> Iterator[tuple[ast.Import | ImportFrom, str, str]]:
    """Yield import nodes and names."""
    for child in iter_import_nodes(node):
        from_module = f"{child.module}." if isinstance(child, ImportFrom) else ""
        for alias in child.names:
            name = alias.asname or alias.name
            fullname = f"{from_module}{alias.name}"
            yield child, name, fullname


def get_assign_name(node: Assign_) -> str | None:
    """Return the name of the assign node."""
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        return node.target.id
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], Name):
        return node.targets[0].id
    if isinstance(node, TypeAlias) and isinstance(node.name, Name):
        return node.name.id
    return None


def _get_docstring(node: AST) -> str | None:
    if not isinstance(node, Expr) or not isinstance(node.value, Constant):
        return None
    doc = node.value.value
    return cleandoc(doc) if isinstance(doc, str) else None


def iter_assign_nodes(node: ast.Module | ClassDef) -> Iterator[Assign_]:
    """Yield assign nodes."""
    assign_node: Assign_ | None = None
    for child in ast.iter_child_nodes(node):
        if isinstance(child, AnnAssign | ast.Assign | TypeAlias):
            if assign_node:
                yield assign_node
            child.__doc__ = None
            assign_node = child
        else:
            if assign_node:
                assign_node.__doc__ = _get_docstring(child)
                yield assign_node
            assign_node = None
    if assign_node:
        assign_node.__doc__ = None
        yield assign_node


def iter_definition_nodes(node: ast.Module | ClassDef) -> Iterator[Def]:
    """Yield definition nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield child


def get_docstring(node: Doc) -> str | None:
    """Return the docstring for the given node or None if no docstring can be found."""
    if isinstance(node, AsyncFunctionDef | FunctionDef | ClassDef | ast.Module):
        return ast.get_docstring(node)
    if isinstance(node, ast.Assign | AnnAssign | TypeAlias):
        return node.__doc__
    msg = f"{node.__class__.__name__!r} can't have docstrings"
    raise TypeError(msg)


@dataclass
class Node:
    """Node class."""

    _node: AST
    name: str
    """Name of item."""
    docstring: str | None
    """Docstring of item."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


@dataclass
class Nodes[T]:
    """Collection of [Node] instance."""

    items: list[T]

    def __getitem__(self, index: int | str) -> T:
        if isinstance(index, int):
            return self.items[index]
        names = [item.name for item in self.items]  # type: ignore  # noqa: PGH003
        return self.items[names.index(index)]

    def __getattr__(self, name: str) -> T:
        return self[name]

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __contains__(self, name: str) -> bool:
        return any(name == item.name for item in self.items)  # type: ignore  # noqa: PGH003

    def __repr__(self) -> str:
        names = ", ".join(f"{item.name!r}" for item in self.items)  # type: ignore  # noqa: PGH003
        return f"{self.__class__.__name__}({names})"


@dataclass(repr=False)
class Import(Node):
    """Import class."""

    _node: ast.Import | ImportFrom
    fullanme: str


@dataclass
class Imports(Nodes[Import]):
    """Imports class."""


def iter_imports(node: ast.Module | ClassDef) -> Iterator[Import]:
    """Yield import nodes."""
    for child, name, fullname in iter_import_node_names(node):
        yield Import(child, name, None, fullname)


def get_imports(node: ast.Module | ClassDef) -> Imports:
    """Return imports in module or class definition."""
    return Imports(list(iter_imports(node)))


ARGS_KIND: dict[_ParameterKind, str] = {
    P.POSITIONAL_ONLY: "posonlyargs",  # before '/', list
    P.POSITIONAL_OR_KEYWORD: "args",  # normal, list
    P.VAR_POSITIONAL: "vararg",  # *args, arg or None
    P.KEYWORD_ONLY: "kwonlyargs",  # after '*' or '*args', list
    P.VAR_KEYWORD: "kwarg",  # **kwargs, arg or None
}


def _iter_parameters(node: FunctionDef_) -> Iterator[tuple[ast.arg, _ParameterKind]]:
    for kind, attr in ARGS_KIND.items():
        if args := getattr(node.args, attr):
            it = args if isinstance(args, list) else [args]
            yield from ((arg, kind) for arg in it)


def _iter_defaults(node: FunctionDef_) -> Iterator[ast.expr | None]:
    args = node.args
    num_positional = len(args.posonlyargs) + len(args.args)
    nones = [None] * num_positional
    yield from [*nones, *args.defaults][-num_positional:]
    yield from args.kw_defaults


@dataclass(repr=False)
class Argument(Node):
    """Argument class."""

    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None


@dataclass(repr=False)
class Parameter(Argument):
    """Parameter class."""

    _node: ast.arg
    kind: _ParameterKind


@dataclass
class Parameters(Nodes[Parameter]):
    """Parameters class."""


def iter_parameters(node: FunctionDef_) -> Iterator[Parameter]:
    """Yield parameters from the function node."""
    it = _iter_defaults(node)
    for arg, kind in _iter_parameters(node):
        default = None if kind in [P.VAR_POSITIONAL, P.VAR_KEYWORD] else next(it)
        yield Parameter(arg, arg.arg, None, arg.annotation, default, kind)


def get_parameters(node: FunctionDef_ | ClassDef) -> Parameters:
    """Return the function parameters."""
    if isinstance(node, ClassDef):
        return Parameters([])
    return Parameters(list(iter_parameters(node)))


@dataclass(repr=False)
class Attribute(Argument):
    """Attribute class."""

    _node: Assign_
    type_params: list[ast.type_param] | None


@dataclass(repr=False)
class Attributes(Nodes[Attribute]):
    """Attributes class."""


def get_annotation(node: Assign_) -> ast.expr | None:
    """Return annotation."""
    if isinstance(node, AnnAssign):
        return node.annotation
    if isinstance(node, TypeAlias):
        return node.value
    return None


def iter_attributes(node: ast.Module | ClassDef) -> Iterator[Attribute]:
    """Yield assign nodes."""
    for assign in iter_assign_nodes(node):
        if not (name := get_assign_name(assign)):
            continue
        ann = get_annotation(assign)
        value = None if isinstance(assign, TypeAlias) else assign.value
        doc = get_docstring(assign)
        type_params = assign.type_params if isinstance(assign, TypeAlias) else None
        yield Attribute(assign, name, doc, ann, value, type_params)


def get_attributes(node: ast.Module | ClassDef) -> Attributes:
    """Return assigns in module or class definition."""
    return Attributes(list(iter_attributes(node)))


@dataclass(repr=False)
class Definition(Node):
    """Definition class for function and class."""

    parameters: Parameters
    decorators: list[ast.expr]
    type_params: list[ast.type_param]
    # raises:


@dataclass(repr=False)
class Function(Definition):
    """Function class."""

    _node: FunctionDef_
    returns: ast.expr | None


@dataclass(repr=False)
class Class(Definition):
    """Class class."""

    _node: ClassDef
    bases: list[ast.expr]
    attributes: Attributes
    functions: Functions


@dataclass(repr=False)
class Functions(Nodes[Function]):
    """Functions class."""


@dataclass(repr=False)
class Classes(Nodes[Class]):
    """Classes class."""


def _get_def_args(
    node: ClassDef | FunctionDef_,
) -> tuple[str, str | None, Parameters, list[ast.expr], list[ast.type_param]]:
    name = node.name
    docstring = get_docstring(node)
    arguments = get_parameters(node)
    decorators = node.decorator_list
    type_params = node.type_params
    return name, docstring, arguments, decorators, type_params


def iter_definitions(node: ast.Module | ClassDef) -> Iterator[Class | Function]:
    """Yield classes or functions."""
    for def_ in iter_definition_nodes(node):
        args = _get_def_args(def_)
        if isinstance(def_, ClassDef):
            attrs = get_attributes(def_)
            _, functions = get_definitions(def_)  # ignore internal classes.
            yield Class(def_, *args, def_.bases, attrs, functions)
        else:
            yield Function(def_, *args, def_.returns)


def get_definitions(node: ast.Module | ClassDef) -> tuple[Classes, Functions]:
    """Return a tuple of ([Classes], [Functions]) instances."""
    classes: list[Class] = []
    functions: list[Function] = []
    for obj in iter_definitions(node):
        if isinstance(obj, Class):
            classes.append(obj)
        else:
            functions.append(obj)
    return Classes(classes), Functions(functions)


@dataclass
class Module(Node):
    """Module class."""

    imports: Imports
    attributes: Attributes
    classes: Classes
    functions: Functions


def get_module(node: ast.Module) -> Module:
    """Return a [Module] instance."""
    docstring = get_docstring(node)
    imports = get_imports(node)
    attrs = get_attributes(node)
    classes, functions = get_definitions(node)
    return Module(node, "", docstring, imports, attrs, classes, functions)


class Transformer(ast.NodeTransformer):  # noqa: D101
    def _rename(self, name: str) -> ast.Name:
        return ast.Name(id=f"__mkapi__.{name}")

    def visit_Name(self, node: ast.Name) -> ast.Name:  # noqa: N802, D102
        return self._rename(node.id)

    def unparse(self, node: ast.expr | ast.type_param) -> str:  # noqa: D102
        return ast.unparse(self.visit(node))


class StringTransformer(Transformer):  # noqa: D101
    def visit_Constant(self, node: ast.Constant) -> ast.Constant | ast.Name:  # noqa: N802, D102
        if isinstance(node.value, str):
            return self._rename(node.value)
        return node


def iter_identifiers(source: str) -> Iterator[tuple[str, bool]]:
    """Yield identifiers as a tuple of (code, isidentifier)."""
    start = 0
    while start < len(source):
        index = source.find("__mkapi__.", start)
        if index == -1:
            yield source[start:], False
            return
        else:
            if index != 0:
                yield source[start:index], False
            start = end = index + 10  # 10 == len("__mkapi__.")
            while end < len(source):
                s = source[end]
                if s == "." or s.isdigit() or s.isidentifier():
                    end += 1
                else:
                    break
            yield source[start:end], True
            start = end
