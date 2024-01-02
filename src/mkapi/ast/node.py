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
    Import,
    ImportFrom,
    Name,
    TypeAlias,
)
from dataclasses import dataclass
from importlib.util import find_spec
from inspect import Parameter, cleandoc
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


def iter_import_nodes(node: AST) -> Iterator[Import | ImportFrom]:
    """Yield import nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, Import | ImportFrom):
            yield child
        elif not isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield from iter_import_nodes(child)


def iter_import_names(node: ast.Module | Def) -> Iterator[tuple[str, str]]:
    """Yield imported names."""
    for child in iter_import_nodes(node):
        from_module = f"{child.module}." if isinstance(child, ImportFrom) else ""
        for alias in child.names:
            name = alias.asname or alias.name
            fullname = f"{from_module}{alias.name}"
            yield name, fullname


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


ARGS_KIND: dict[_ParameterKind, str] = {
    Parameter.POSITIONAL_ONLY: "posonlyargs",  # before '/', list
    Parameter.POSITIONAL_OR_KEYWORD: "args",  # normal, list
    Parameter.VAR_POSITIONAL: "vararg",  # *args, arg or None
    Parameter.KEYWORD_ONLY: "kwonlyargs",  # after '*' or '*args', list
    Parameter.VAR_KEYWORD: "kwarg",  # **kwargs, arg or None
}


def _iter_arguments(node: FunctionDef_) -> Iterator[tuple[ast.arg, _ParameterKind]]:
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


@dataclass
class _Item:
    name: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


@dataclass
class _Items[T]:
    items: list[T]

    def __getitem__(self, index: int) -> T:
        return self.items[index]

    def __getattr__(self, name: str) -> T:
        names = [elem.name for elem in self.items]  # type: ignore  # noqa: PGH003
        return self.items[names.index(name)]

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __repr__(self) -> str:
        names = ", ".join(f"{elem.name!r}" for elem in self.items)  # type: ignore  # noqa: PGH003
        return f"{self.__class__.__name__}({names})"


@dataclass(repr=False)
class Argument(_Item):
    """Argument class."""

    annotation: ast.expr | None
    default: ast.expr | None
    kind: _ParameterKind


@dataclass
class Arguments(_Items[Argument]):
    """Arguments class."""


def iter_arguments(node: FunctionDef_) -> Iterator[Argument]:
    """Yield arguments from the function node."""
    it = _iter_defaults(node)
    for arg, kind in _iter_arguments(node):
        if kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]:
            default = None
        else:
            default = next(it)
        yield Argument(arg.arg, arg.annotation, default, kind)


def get_arguments(node: FunctionDef_ | ClassDef) -> Arguments:
    """Return the function arguments."""
    if isinstance(node, ClassDef):
        return Arguments([])
    return Arguments(list(iter_arguments(node)))


@dataclass(repr=False)
class Attribute(_Item):
    """Attribute class."""

    annotation: ast.expr | None
    value: ast.expr | None
    docstring: str | None
    kind: type[Assign_]
    type_params: list[ast.type_param] | None


@dataclass(repr=False)
class Attributes(_Items[Attribute]):
    """Assigns class."""


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
        annotation = get_annotation(assign)
        value = None if isinstance(assign, TypeAlias) else assign.value
        docstring = get_docstring(assign)
        type_params = assign.type_params if isinstance(assign, TypeAlias) else None
        yield Attribute(name, annotation, value, docstring, type(assign), type_params)


def get_attributes(node: ast.Module | ClassDef) -> Attributes:
    """Return assigns in module or class definition."""
    return Attributes(list(iter_attributes(node)))


@dataclass(repr=False)
class _Def(_Item):
    docstring: str | None
    args: Arguments
    decorators: list[ast.expr]
    type_params: list[ast.type_param]


@dataclass(repr=False)
class Function(_Def):
    """Function class."""

    returns: ast.expr | None
    kind: type[FunctionDef_]


@dataclass(repr=False)
class Class(_Def):
    """Class class."""

    bases: list[ast.expr]
    attrs: Attributes


@dataclass(repr=False)
class Functions(_Items[Function]):
    """Functions class."""


@dataclass(repr=False)
class Classes(_Items[Class]):
    """Classes class."""


def _get_def_args(
    node: ClassDef | FunctionDef_,
) -> tuple[str, str | None, Arguments, list[ast.expr], list[ast.type_param]]:
    name = node.name
    docstring = get_docstring(node)
    args = get_arguments(node)
    decorators = node.decorator_list
    type_params = node.type_params
    return name, docstring, args, decorators, type_params


def iter_definitions(module: ast.Module) -> Iterator[Class | Function]:
    """Yield classes or functions."""
    for node in iter_definition_nodes(module):
        args = _get_def_args(node)
        if isinstance(node, ClassDef):
            attrs = get_attributes(node)
            yield Class(*args, node.bases, attrs)
        else:
            yield Function(*args, node.returns, type(node))


@dataclass
class Module:
    """Module class."""

    docstring: str | None
    imports: dict[str, str]
    attrs: Attributes
    classes: Classes
    functions: Functions


def get_module(node: ast.Module) -> Module:
    """Return a [Module] instance."""
    docstring = get_docstring(node)
    imports = dict(iter_import_names(node))
    attrs = get_attributes(node)
    classes: list[Class] = []
    functions: list[Function] = []
    for obj in iter_definitions(node):
        if isinstance(obj, Class):
            classes.append(obj)
        else:
            functions.append(obj)
    return Module(docstring, imports, attrs, Classes(classes), Functions(functions))
