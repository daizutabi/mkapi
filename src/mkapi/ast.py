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
    ImportFrom,
    Name,
    NodeTransformer,
    Raise,
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

type Import_ = ast.Import | ImportFrom
type FunctionDef_ = AsyncFunctionDef | FunctionDef
type Def = FunctionDef_ | ClassDef
type Assign_ = Assign | AnnAssign | TypeAlias

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


@dataclass
class Node:  # noqa: D101
    _node: ast.AST
    name: str
    docstring: str | None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


@dataclass(repr=False)
class Import(Node):  # noqa: D101
    _node: ast.Import | ImportFrom
    fullname: str


def iter_import_nodes(node: AST) -> Iterator[Import_]:
    """Yield import nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Import | ImportFrom):
            yield child
        elif not isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield from iter_import_nodes(child)


def iter_imports(node: ast.Module) -> Iterator[Import]:
    """Yield import nodes and names."""
    for child in iter_import_nodes(node):
        from_module = f"{child.module}." if isinstance(child, ImportFrom) else ""
        for alias in child.names:
            name = alias.asname or alias.name
            fullname = f"{from_module}{alias.name}"
            yield Import(child, name, None, fullname)


@dataclass(repr=False)
class Attribute(Node):  # noqa: D101
    _node: Assign_
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    type_params: list[ast.type_param] | None


def _get_pseudo_docstring(node: AST) -> str | None:
    if not isinstance(node, Expr) or not isinstance(node.value, Constant):
        return None
    doc = node.value.value
    return cleandoc(doc) if isinstance(doc, str) else None


def iter_assign_nodes(node: ast.Module | ClassDef) -> Iterator[Assign_]:
    """Yield assign nodes."""
    assign_node: Assign_ | None = None
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


def get_assign_name(node: Assign_) -> str | None:
    """Return the name of the assign node."""
    if isinstance(node, AnnAssign) and isinstance(node.target, Name):
        return node.target.id
    if isinstance(node, Assign) and isinstance(node.targets[0], Name):
        return node.targets[0].id
    if isinstance(node, TypeAlias) and isinstance(node.name, Name):
        return node.name.id
    return None


def get_type(node: Assign_) -> ast.expr | None:
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
        type_ = get_type(assign)
        value = None if isinstance(assign, TypeAlias) else assign.value
        type_params = assign.type_params if isinstance(assign, TypeAlias) else None
        yield Attribute(assign, name, assign.__doc__, type_, value, type_params)


@dataclass(repr=False)
class Parameter(Node):  # noqa: D101
    _node: ast.arg
    type: ast.expr | None  #   # noqa: A003
    default: ast.expr | None
    kind: _ParameterKind


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


def iter_parameters(node: FunctionDef_) -> Iterator[Parameter]:
    """Yield parameters from the function node."""
    it = _iter_defaults(node)
    for arg, kind in _iter_parameters(node):
        default = None if kind in [P.VAR_POSITIONAL, P.VAR_KEYWORD] else next(it)
        yield Parameter(arg, arg.arg, None, arg.annotation, default, kind)


@dataclass(repr=False)
class Definition(Node):  # noqa: D101
    parameters: list[Parameter]
    decorators: list[ast.expr]
    type_params: list[ast.type_param]
    raises: list[ast.expr]


@dataclass(repr=False)
class Function(Definition):  # noqa: D101
    _node: FunctionDef_
    returns: ast.expr | None


@dataclass(repr=False)
class Class(Definition):  # noqa: D101
    _node: ClassDef
    bases: list[ast.expr]
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]

    def get(self, name: str) -> Class | Function:  # noqa: D102
        names = [cls.name for cls in self.classes]
        if name in names:
            return self.classes[names.index(name)]
        names = [func.name for func in self.functions]
        if name in names:
            return self.functions[names.index(name)]
        raise NameError


def iter_definition_nodes(node: ast.Module | ClassDef) -> Iterator[Def]:
    """Yield definition nodes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, AsyncFunctionDef | FunctionDef | ClassDef):
            yield child


def iter_raise_nodes(node: FunctionDef_) -> Iterator[Raise]:
    """Yield raise nodes."""
    for child in ast.walk(node):
        if isinstance(child, Raise):
            yield child


def _get_def_args(
    node: Def,
) -> tuple[str, str | None, list[Parameter], list[ast.expr], list[ast.type_param]]:
    name = node.name
    docstring = ast.get_docstring(node)
    parameters = [] if isinstance(node, ClassDef) else list(iter_parameters(node))
    decorators = node.decorator_list
    type_params = node.type_params
    return name, docstring, parameters, decorators, type_params


def iter_definitions(node: ast.Module | ClassDef) -> Iterator[Class | Function]:
    """Yield classes or functions."""
    for def_node in iter_definition_nodes(node):
        args = _get_def_args(def_node)
        if isinstance(def_node, ClassDef):
            attrs = list(iter_attributes(def_node))
            classes, functions = get_definitions(def_node)
            yield Class(def_node, *args, [], def_node.bases, attrs, classes, functions)
        else:
            raises = [r.exc for r in iter_raise_nodes(def_node) if r.exc]
            yield Function(def_node, *args, raises, def_node.returns)


def get_definitions(node: ast.Module | ClassDef) -> tuple[list[Class], list[Function]]:
    """Return a tuple of (list[Class], list[Function])."""
    classes: list[Class] = []
    functions: list[Function] = []
    for definition in iter_definitions(node):
        if isinstance(definition, Class):
            classes.append(definition)
        else:
            functions.append(definition)
    return classes, functions


@dataclass
class Module(Node):  # noqa: D101
    imports: list[Import]
    attributes: list[Attribute]
    classes: list[Class]
    functions: list[Function]

    def get(self, name: str) -> Class | Function:  # noqa: D102
        names = [cls.name for cls in self.classes]
        if name in names:
            return self.classes[names.index(name)]
        names = [func.name for func in self.functions]
        if name in names:
            return self.functions[names.index(name)]
        raise NameError


def get_module(node: ast.Module) -> Module:
    """Return a [Module] instance."""
    docstring = ast.get_docstring(node)
    imports = list(iter_imports(node))
    attrs = list(iter_attributes(node))
    classes, functions = get_definitions(node)
    return Module(node, "", docstring, imports, attrs, classes, functions)


class Transformer(NodeTransformer):  # noqa: D101
    def _rename(self, name: str) -> Name:
        return Name(id=f"__mkapi__.{name}")

    def visit_Name(self, node: Name) -> Name:  # noqa: N802, D102
        return self._rename(node.id)

    def unparse(self, node: ast.expr | ast.type_param) -> str:  # noqa: D102
        return ast.unparse(self.visit(node))


class StringTransformer(Transformer):  # noqa: D101
    def visit_Constant(self, node: Constant) -> Constant | Name:  # noqa: N802, D102
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
