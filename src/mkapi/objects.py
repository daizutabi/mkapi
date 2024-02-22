"""Object module."""
from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast
import mkapi.nodes
from mkapi.ast import is_classmethod, is_function, is_property, is_staticmethod
from mkapi.nodes import Import, _parse, is_dataclass, resolve, resolve_from_module
from mkapi.utils import (
    cache,
    get_module_node,
    get_module_node_source,
    is_package,
)

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from inspect import _ParameterKind


@dataclass
class Parameter:
    name: str
    type: ast.expr | None
    default: ast.expr | None
    kind: _ParameterKind

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


objects: dict[str, Module | Object] = cache({})


@dataclass(repr=False)
class Object:
    name: str
    node: ast.AST
    qualname: str
    module: str
    doc: str | None
    kind: str = field(init=False)

    def __post_init__(self):
        self.kind = _get_kind(self)
        fullname = _get_fullname(self)
        objects[fullname] = self

    def __repr__(self) -> str:
        fullname = f"{self.module}.{self.qualname}"
        return f"{self.__class__.__name__}({fullname!r})"


@dataclass(repr=False)
class Attribute(Object):
    node: ast.AnnAssign | ast.Assign | TypeAlias  # type: ignore
    type: ast.expr | None
    default: ast.expr | None


@dataclass(repr=False)
class Property(Object):
    node: ast.FunctionDef | ast.AsyncFunctionDef
    type: ast.expr | None


@dataclass(repr=False)
class Callable(Object):
    parameters: list[Parameter]
    raises: list[ast.expr]
    dict: dict[str, Object]

    def get(self, name) -> Object | None:
        return self.dict.get(name)


@dataclass(repr=False)
class Class(Callable):
    node: ast.ClassDef


@dataclass(repr=False)
class Function(Callable):
    node: ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Module:
    name: str
    node: ast.Module | None
    doc: str | None
    dict: dict[str, Object | Import]
    source: str
    kind: str = field(init=False)

    def __post_init__(self):
        self.kind = _get_kind(self)
        objects[self.name] = self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"

    def get(self, name) -> Module | Object | Import | None:
        return self.dict.get(name)


@dataclass(repr=False)
class _Module:
    name: str
    node: ast.Module | None
    kind: str = field(init=False)

    def __post_init__(self):
        self.kind = _get_kind(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


def _create_object(node: ast.AST, module: str, parent: str | None) -> Object | None:
    if isinstance(node, ast.ClassDef):
        return create_class(node, module, parent)

    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        if is_function(node):
            return create_function(node, module, parent)

        if is_property(node):
            return create_property(node, module, parent)

    if isinstance(node, ast.AnnAssign | ast.Assign | TypeAlias):  # noqa: SIM102
        if name := mkapi.ast.get_assign_name(node):
            return create_attribute(name, node, module, parent)

    return None


def _iter_objects(node: ast.AST, module: str, parent: str) -> Iterator[Object]:
    for child in mkapi.ast.iter_child_nodes(node):
        if obj := _create_object(child, module, parent):
            yield obj


def create_class(node: ast.ClassDef, module: str, parent: str | None) -> Class:
    name = node.name
    qualname = f"{parent}.{name}" if parent else name
    doc = ast.get_docstring(node)

    dict_ = {obj.name: obj for obj in _iter_objects(node, module, name)}

    for base in get_base_classes(name, module):
        for name, obj in base.dict.items():
            dict_.setdefault(name, obj)

    cls = Class(node.name, node, qualname, module, doc, [], [], dict_)

    if is_dataclass(node, module):  # noqa: SIM108
        params = iter_dataclass_parameters(cls)
    else:
        params = iter_init_parameters(cls)

    cls.parameters = list(params)

    return cls


@cache
def get_base_classes(name: str, module: str) -> list[Class]:
    return list(iter_base_classes(name, module))


def iter_base_classes(name: str, module: str) -> Iterator[Class]:
    for basename, basemodule in _iter_base_classes(name, module):
        if cls := objects.get(f"{basemodule}.{basename}"):
            if isinstance(cls, Class):
                yield cls

        elif cls := _create_base_class(basename, basemodule):
            yield cls


def _create_base_class(name: str, module: str) -> Class | None:
    if node := get_module_node(module):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef) and child.name == name:
                return create_class(child, module, None)
    return None


def iter_init_parameters(cls: Class) -> Iterator[Parameter]:
    if (func := cls.get("__init__")) and isinstance(func, Function):
        yield from func.parameters[1:]


def iter_dataclass_parameters(cls: Class) -> Iterator[Parameter]:
    if (obj := _get_object(cls.name, cls.module)) and inspect.isclass(obj):
        for param in inspect.signature(obj).parameters.values():
            if (assign := cls.get(param.name)) and isinstance(assign, Attribute):
                args = (assign.name, assign.type, assign.default)
                yield Parameter(*args, param.kind)

            else:
                raise NotImplementedError


def create_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: str | None,
) -> Function:
    name = node.name
    qualname = f"{parent}.{name}" if parent else name
    doc = ast.get_docstring(node)

    params = [Parameter(*args) for args in mkapi.ast.iter_parameters(node)]
    raises = list(mkapi.ast.iter_raises(node))

    dict_ = {obj.name: obj for obj in _iter_objects(node, module, name)}

    return Function(node.name, node, qualname, module, doc, params, raises, dict_)


def create_property(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: str | None,
) -> Property:
    name = node.name
    qualname = f"{parent}.{name}" if parent else name
    doc = ast.get_docstring(node)

    return Property(node.name, node, qualname, module, doc, node.returns)


def create_attribute(
    name: str,
    node: ast.AnnAssign | ast.Assign | TypeAlias,  # type: ignore
    module: str,
    parent: str | None,
) -> Attribute:
    qualname = f"{parent}.{name}" if parent else name
    doc = node.__doc__

    type_ = mkapi.ast.get_assign_type(node)
    default = None if TypeAlias and isinstance(node, TypeAlias) else node.value

    return Attribute(name, node, qualname, module, doc, type_, default)


def _create_module(name: str, node: ast.Module, source: str) -> Module:
    doc = ast.get_docstring(node)

    dict_ = {}
    for name_, child in _parse(node, name):
        if isinstance(child, mkapi.nodes.Module):
            dict_[name_] = _Module(child.name, child.node)

        elif child.module and (obj := _create_object(child.node, child.module, None)):
            dict_[name_] = obj

    module = Module(name, node, doc, dict_, source)

    it = (child for child in walk(module) if isinstance(child, Attribute) and child.module == name)
    _add_doc_comment(it, module.source)

    return module


@cache
def create_module(name: str) -> Module | None:
    if not (node_source := get_module_node_source(name)):
        return None

    return _create_module(name, *node_source)


def walk(obj: Module | Class | Function) -> Iterator[Module | Object | Import]:
    yield obj

    members = obj.dict or {}

    for member in members.values():
        if isinstance(member, Module | Class | Function):
            yield from walk(member)
        else:
            yield member


def _add_doc_comment(assigns: Iterable[Attribute], source: str) -> None:
    lines = source.splitlines()

    for assign in assigns:
        if assign.doc:
            continue

        node = assign.node

        line = lines[node.lineno - 1][node.end_col_offset :].strip()

        if line.startswith("#:"):
            assign.doc = line[2:].strip()

        elif node.lineno > 1:
            line = lines[node.lineno - 2][node.col_offset :]
            if line.startswith("#:"):
                assign.doc = line[2:].strip()


# @cache
# def _get_module_name(module: str) -> str | None:
#     try:
#         return importlib.import_module(module).__name__
#     except ModuleNotFoundError:
#         return


@cache
def _get_object(name: str, module: str) -> object | None:
    try:
        obj = importlib.import_module(module)
    except ModuleNotFoundError:
        return

    members = dict(inspect.getmembers(obj))
    return members.get(name)


def _iter_base_classes(name: str, module: str) -> Iterator[tuple[str, str]]:
    if not module:
        return

    if (obj := _get_object(name, module)) and inspect.isclass(obj):
        for base in obj.__bases__:
            if base.__module__ != "builtins":
                yield base.__name__, base.__module__


def get_source(obj: Module | Object) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        return obj.source

    if module := create_module(obj.module):
        return ast.get_source_segment(module.source, obj.node)

    return None


def resolve_from_object(
    name: str,
    obj: Module | Object,
) -> str | None:
    """Return fullname from object."""
    if isinstance(obj, Module | Class | Function):
        for name_, child in obj.dict.items():
            if name_ == name:
                return _get_fullname(child)

    if isinstance(obj, Module):
        return resolve_from_module(name, obj.name)

    if "." not in name:
        return resolve_from_module(name, obj.module)

    parent, attr = name.rsplit(".", maxsplit=1)

    if parent_obj := objects.get(parent):
        return resolve_from_object(name, parent_obj)

    if obj.name == parent:
        return resolve_from_object(attr, obj)

    return resolve(name)


def _get_fullname(obj: Module | Object | Import) -> str:
    if isinstance(obj, Module):
        return f"{obj.name}"

    if isinstance(obj, Object):
        return f"{obj.module}.{obj.name}"

    return obj.fullname  # import


def _get_kind_function(func: Function) -> str:
    if is_classmethod(func.node):
        return "classmethod"

    if is_staticmethod(func.node):
        return "staticmethod"

    return "method" if "." in func.qualname else "function"


def _get_kind(obj: Object | Module | _Module) -> str:
    """Return kind."""
    if isinstance(obj, Module | _Module):
        return "package" if is_package(obj.name) else "module"

    if isinstance(obj, Class):
        return "dataclass" if is_dataclass(obj.node, obj.module) else "class"

    if isinstance(obj, Function):
        return _get_kind_function(obj)

    return obj.__class__.__name__.lower()


# def is_empty(obj: Object) -> bool:
#     """Return True if a [Object] instance is empty."""
#     if isinstance(obj, Attribute) and not obj.doc.sections:
#         return True

#     if not docstrings.is_empty(obj.doc):
#         return False

#     if isinstance(obj, Function) and obj.name.str.startswith("_"):
#         return True
