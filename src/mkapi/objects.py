"""Object module."""
from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeGuard, TypeVar

import mkapi.ast
import mkapi.nodes
from mkapi.ast import is_classmethod, is_function, is_property, is_staticmethod
from mkapi.nodes import _parse, is_dataclass, resolve, resolve_from_module
from mkapi.utils import (
    cache,
    get_module_name,
    get_module_node,
    get_module_node_source,
    get_module_source,
    is_package,
    iter_identifiers,
    iter_parent_module_names,
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


objects: dict[str, Object] = cache({})
aliases: dict[str, list[str]] = cache({})


def _register_object(obj: Object, name: str | None = None):
    fullname = get_fullname(obj)
    objects[name or fullname] = obj

    aliases.setdefault(fullname, [])

    if name and name not in aliases[fullname]:
        aliases[fullname].append(name)


@dataclass
class Object:
    name: str
    node: ast.AST
    doc: str | None
    kind: str = field(init=False)

    def __post_init__(self):
        self.kind = get_kind(self)
        _register_object(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


@dataclass(repr=False)
class Member(Object):
    qualname: str
    module: str


@dataclass(repr=False)
class Attribute(Member):
    node: ast.AnnAssign | ast.Assign | TypeAlias  # type: ignore
    type: ast.expr | None
    default: ast.expr | None


@dataclass(repr=False)
class Property(Member):
    node: ast.FunctionDef | ast.AsyncFunctionDef
    type: ast.expr | None


T = TypeVar("T")


@dataclass(repr=False)
class Dict(Object):
    dict: dict[str, Object]

    def __post_init__(self):
        super().__post_init__()

        fullname = get_fullname(self)
        for name, child in self.dict.items():
            _register_object(child, f"{fullname}.{name}")

    def get(self, name) -> Object | None:
        return self.dict.get(name)

    def objects(self, type_: type[T]) -> list[tuple[str, T]]:
        it = self.dict.items()
        return [(name, obj) for (name, obj) in it if isinstance(obj, type_)]

    def iter_objects(self, type_: type[T] = type[Object]) -> Iterator[T]:
        for obj in self.dict.values():
            if isinstance(obj, type_):
                yield obj
            if isinstance(obj, Dict):
                yield from obj.iter_objects(type_)


@dataclass(repr=False)
class Callable(Member, Dict):
    parameters: list[Parameter]
    raises: list[ast.expr]


@dataclass(repr=False)
class Class(Callable):
    node: ast.ClassDef


@dataclass(repr=False)
class Function(Callable):
    node: ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Module(Dict):
    node: ast.Module | None


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
    doc = ast.get_docstring(node)
    qualname = f"{parent}.{node.name}" if parent else node.name
    dict_ = {obj.name: obj for obj in _iter_objects(node, module, qualname)}

    if (func := dict_.get("__init__")) and isinstance(func, Function):
        for name, obj in iter_init_attributes(func, qualname):
            dict_.setdefault(name, obj)

    for base in get_base_classes(node.name, module):
        for name, obj in base.dict.items():
            dict_.setdefault(name, obj)

    cls = Class(node.name, node, doc, dict_, qualname, module, [], [])

    if is_dataclass(node, module):
        params = iter_dataclass_parameters(cls)
        cls.parameters.extend(params)

    else:
        params = iter_init_parameters(cls)
        cls.parameters.extend(params)

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


def iter_init_attributes(func: Function, parent: str) -> Iterator[tuple[str, Attribute]]:
    self = func.parameters[0].name

    for name, obj in list(func.dict.items()):
        if isinstance(obj, Attribute) and name.startswith(f"{self}."):
            name_ = name[len(self) + 1 :]
            attr = create_attribute(name_, obj.node, obj.module, parent)
            yield name_, attr
            del func.dict[name]


def iter_dataclass_parameters(cls: Class) -> Iterator[Parameter]:
    if (obj := _get_object(cls.name, cls.module)) and inspect.isclass(obj):
        for param in inspect.signature(obj).parameters.values():
            if (assign := cls.get(param.name)) and isinstance(assign, Attribute):
                args = (assign.name, assign.type, assign.default)
                yield Parameter(*args, param.kind)

            else:
                raise NotImplementedError


def iter_init_parameters(cls: Class) -> Iterator[Parameter]:
    if (func := cls.get("__init__")) and isinstance(func, Function):
        yield from func.parameters[1:]


def create_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: str | None,
) -> Function:
    doc = ast.get_docstring(node)
    qualname = f"{parent}.{node.name}" if parent else node.name
    dict_ = {obj.name: obj for obj in _iter_objects(node, module, qualname)}

    params = [Parameter(*args) for args in mkapi.ast.iter_parameters(node)]
    raises = list(mkapi.ast.iter_raises(node))

    return Function(node.name, node, doc, dict_, qualname, module, params, raises)


def create_property(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: str | None,
) -> Property:
    doc = ast.get_docstring(node)
    qualname = f"{parent}.{node.name}" if parent else node.name

    return Property(node.name, node, doc, qualname, module, node.returns)


def create_attribute(
    name: str,
    node: ast.AnnAssign | ast.Assign | TypeAlias,  # type: ignore
    module: str,
    parent: str | None,
) -> Attribute:
    doc = node.__doc__
    qualname = f"{parent}.{name}" if parent else name

    type_ = mkapi.ast.get_assign_type(node)
    default = None if TypeAlias and isinstance(node, TypeAlias) else node.value

    return Attribute(name, node, doc, qualname, module, type_, default)


def _create_module(name: str, node: ast.Module, source: str | None = None) -> Module:
    doc = ast.get_docstring(node)

    dict_ = {}
    for name_, child in _parse(node, name):
        if isinstance(child, mkapi.nodes.Module):
            dict_[name_] = Module(child.name, child.node, None, {})

        elif obj := _create_object(child.node, child.module, None):
            dict_[name_] = obj

    module = Module(name, node, doc, dict_)

    if source:
        lines = source.splitlines()
        for attr in module.iter_objects(Attribute):
            if attr.doc or attr.module != name:
                continue
            if doc := _get_doc_comment(attr.node, lines):
                attr.doc = doc

    return module


def _get_doc_comment(node: ast.AST, lines: list[str]) -> str | None:
    line = lines[node.lineno - 1][node.end_col_offset :].strip()

    if line.startswith("#:"):
        return line[2:].strip()

    if node.lineno > 1:
        line = lines[node.lineno - 2][node.col_offset :]
        if line.startswith("#:"):
            return line[2:].strip()

    return None


@cache
def create_module(name: str) -> Module | None:
    if not (node_source := get_module_node_source(name)):
        return None

    return _create_module(name, *node_source)


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
                basename = next(iter_identifiers(base.__name__))[0]
                yield basename, base.__module__


@cache
def get_object(fullname: str) -> Object | None:
    if fullname in objects:
        return objects[fullname]

    for module in iter_parent_module_names(fullname):
        if create_module(module) and fullname in objects:
            return objects[fullname]

    return None


def resolve_from_object(name: str, obj: Object) -> str | None:
    """Return fullname from object."""
    if isinstance(obj, Dict) and (child := obj.get(name)):
        return get_fullname(child)

    if isinstance(obj, Module):
        return resolve_from_module(name, obj.name)

    if "." not in name and isinstance(obj, Member):
        return resolve_from_module(name, obj.module)

    parent, name_ = name.rsplit(".", maxsplit=1)

    if obj_ := objects.get(parent):
        return resolve_from_object(name, obj_)

    if obj.name == parent:
        return resolve_from_object(name_, obj)

    return resolve(name)


def get_fullname(obj: Object) -> str:
    if isinstance(obj, Module):
        return get_module_name(obj.name)

    if isinstance(obj, Member):
        module = get_module_name(obj.module) if obj.module else "__mkapi__"
        return f"{module}.{obj.qualname}"

    return obj.name


def _get_kind_function(func: Function) -> str:
    if is_classmethod(func.node):
        return "classmethod"

    if is_staticmethod(func.node):
        return "staticmethod"

    return "method" if "." in func.qualname else "function"


def get_kind(obj: Object | Module) -> str:
    """Return kind."""
    if isinstance(obj, Module):
        return "package" if is_package(obj.name) else "module"

    if isinstance(obj, Class):
        return "dataclass" if is_dataclass(obj.node, obj.module) else "class"

    if isinstance(obj, Function):
        return _get_kind_function(obj)

    return obj.__class__.__name__.lower()


def get_source(obj: Module | Member) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        return get_module_source(obj.name)

    if source := get_module_source(obj.module):
        return ast.get_source_segment(source, obj.node)

    return None


# def is_empty(obj: Object) -> bool:
#     """Return True if a [Object] instance is empty."""
#     if isinstance(obj, Attribute) and not obj.doc.sections:
#         return True

#     if not docstrings.is_empty(obj.doc):
#         return False

#     if isinstance(obj, Function) and obj.name.str.startswith("_"):
#         return True
