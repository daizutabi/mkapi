"""Object module."""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

import mkapi.ast
import mkapi.nodes
import mkapi.utils
from mkapi.ast import (
    Parameter,
    TypeAlias,
    get_assign_name,
    get_assign_type,
    is_assign,
    is_classmethod,
    is_function,
    is_property,
    is_staticmethod,
    iter_parameters,
    iter_raises,
)
from mkapi.docs import create_doc, create_doc_comment, is_empty, split_type
from mkapi.nodes import get_fullname, parse
from mkapi.utils import (
    cache,
    get_module_node,
    get_module_node_source,
    get_module_source,
    get_object_from_module,
    is_dataclass,
    is_package,
    split_name,
)

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Callable, Iterator

    from mkapi.docs import Doc


def _qualname(name: str, parent: Parent | None) -> str:
    return f"{parent.qualname}.{name}" if parent else name


def _fullname(name: str, module: str | None, parent: Parent | None) -> str:
    qualname = _qualname(name, parent)
    return f"{module}.{qualname}" if module else name


@dataclass
class Object:
    name: str
    node: AST
    module: str
    parent: Parent | None
    qualname: str = field(init=False)
    fullname: str = field(init=False)
    doc: Doc = field(init=False)

    def __post_init__(self):
        self.qualname = _qualname(self.name, self.parent)
        self.fullname = _fullname(self.name, self.module, self.parent)
        objects[self.fullname] = self

        node = self.node
        types = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        text = ast.get_docstring(node) if isinstance(node, types) else node.__doc__
        self.doc = create_doc(text)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


objects: dict[str, Object] = cache({})


def iter_child_objects(
    node: AST,
    module: str,
    parent: Parent | None,
) -> Iterator[Object]:
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            yield create_class(child, module, parent)

        elif is_function(child):
            yield create_function(child, module, parent)

        elif is_property(child):
            yield create_property(child, module, parent)

        elif is_assign(child) and (name := get_assign_name(child)):
            yield create_attribute(name, child, module, parent)


@dataclass(repr=False)
class Type(Object):
    type: ast.expr | None

    def __post_init__(self):
        super().__post_init__()
        split_type(self.doc)


@dataclass(repr=False)
class Attribute(Type):
    node: ast.AnnAssign | ast.Assign | TypeAlias
    default: ast.expr | None


@dataclass(repr=False)
class Property(Type):
    node: ast.FunctionDef | ast.AsyncFunctionDef


def create_attribute(
    name: str,
    node: ast.AnnAssign | ast.Assign | TypeAlias,
    module: str,
    parent: Parent | None,
) -> Attribute:
    type_ = get_assign_type(node)
    default = None if TypeAlias and isinstance(node, TypeAlias) else node.value

    return Attribute(name, node, module, parent, type_, default)


def create_property(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: Parent | None,
) -> Property:
    return Property(node.name, node, module, parent, node.returns)


T = TypeVar("T")


@dataclass(repr=False)
class Parent(Object):
    children: dict[str, Object] = field(default_factory=dict, init=False)

    def get(self, name: str, type_: type[T] = Object) -> T | None:
        child = self.children.get(name)

        return child if isinstance(child, type_) else None

    def get_children(self, type_: type[T] = Object) -> list[tuple[str, T]]:
        it = self.children.items()

        return [(name, obj) for (name, obj) in it if isinstance(obj, type_)]


def iter_objects(obj: Parent, type_: type[T] = Object) -> Iterator[T]:
    for child in obj.children.values():
        if isinstance(child, type_):
            yield child

        if isinstance(child, Parent):
            yield from iter_objects(child, type_)


@dataclass(repr=False)
class Definition(Parent):
    parameters: list[Parameter]
    raises: list[ast.expr]

    def __post_init__(self):
        super().__post_init__()

        for obj in iter_child_objects(self.node, self.module, self):
            self.children[obj.name] = obj


@dataclass(repr=False)
class Class(Definition):
    node: ast.ClassDef


@dataclass(repr=False)
class Function(Definition):
    node: ast.FunctionDef | ast.AsyncFunctionDef


def create_class(node: ast.ClassDef, module: str, parent: Parent | None) -> Class:
    fullname = _fullname(node.name, module, parent)
    if (cls := objects.get(fullname)) and isinstance(cls, Class):
        return cls

    cls = Class(node.name, node, module, parent, [], [])

    init = cls.children.get("__init__")

    if isinstance(init, Function):
        for attr in iter_attributes_from_function(init, cls):
            cls.children.setdefault(attr.name, attr)

    for base in get_base_classes(node.name, module):
        for name, obj in base.get_children():
            cls.children.setdefault(name, obj)

    if is_dataclass(node.name, module):
        params = iter_parameters_from_dataclass(cls)
        cls.parameters.extend(params)

    elif isinstance(init, Function):
        params = init.parameters[1:]
        cls.parameters.extend(params)

    return cls


@cache
def get_base_classes(name: str, module: str) -> list[Class]:
    bases = []

    for basename, basemodule in mkapi.utils.get_base_classes(name, module):
        if cls := objects.get(f"{basemodule}.{basename}"):
            if isinstance(cls, Class):
                bases.append(cls)

        elif cls := _create_class_from_name(basename, basemodule):
            bases.append(cls)

    return bases


def _create_class_from_name(name: str, module: str) -> Class | None:
    if node := get_module_node(module):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef) and child.name == name:
                return create_class(child, module, None)

    return None


def iter_attributes_from_function(func: Function, parent: Parent) -> Iterator[Attribute]:
    self = func.parameters[0].name

    for name, obj in func.get_children(Attribute):
        if name.startswith(f"{self}."):
            name_ = name[len(self) + 1 :]
            yield create_attribute(name_, obj.node, obj.module, parent)
            del func.children[name]


def iter_parameters_from_dataclass(cls: Class) -> Iterator[Parameter]:
    obj = get_object_from_module(cls.name, cls.module)

    if inspect.isclass(obj):
        for param in inspect.signature(obj).parameters.values():
            if (assign := cls.get(param.name)) and isinstance(assign, Attribute):
                args = (assign.name, assign.type, assign.default)
                yield Parameter(*args, param.kind)

            else:
                raise NotImplementedError


def create_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: Parent | None,
) -> Function:
    params = list(iter_parameters(node))
    raises = list(iter_raises(node))

    return Function(node.name, node, module, parent, params, raises)


@dataclass(repr=False)
class Module(Parent):
    node: ast.Module
    module: None = field(default=None, init=False)
    parent: None = field(default=None, init=False)

    def __post_init__(self):
        super().__post_init__()

        for obj in iter_child_objects(self.node, self.name, None):
            self.children[obj.name] = obj


@cache
def create_module(
    name: str,
    node: ast.Module | None = None,
    source: str | None = None,
) -> Module | None:
    if not node:
        if node_source := get_module_node_source(name):
            node, source = node_source
        else:
            return None

    module = Module(name, node)

    if source:
        lines = source.splitlines()
        for attr in iter_objects(module, Attribute):
            if not is_empty(attr.doc) or attr.module != name:
                continue

            if doc := _create_doc_comment(attr.node, lines):
                attr.doc = doc

    return module


def _create_doc_comment(node: AST, lines: list[str]) -> Doc | None:
    line = lines[node.lineno - 1][node.end_col_offset :].strip()

    if line.startswith("#:"):
        return create_doc_comment(line[2:].strip())

    if node.lineno > 1:
        line = lines[node.lineno - 2][node.col_offset :]
        if line.startswith("#:"):
            return create_doc_comment(line[2:].strip())

    return None


def get_kind(obj: Object | Module) -> str:
    """Return kind."""
    if isinstance(obj, Module):
        return "package" if is_package(obj.name) else "module"

    if isinstance(obj, Class):
        return "dataclass" if is_dataclass(obj.name, obj.module) else "class"

    if isinstance(obj, Function):
        if is_classmethod(obj.node):
            return "classmethod"

        if is_staticmethod(obj.node):
            return "staticmethod"

        return "method" if "." in obj.qualname else "function"

    return obj.__class__.__name__.lower()


def get_source(obj: Object) -> str | None:
    """Return the source code of an object."""
    if isinstance(obj, Module):
        return get_module_source(obj.name)

    if source := get_module_source(obj.module):
        return ast.get_source_segment(source, obj.node)

    return None


def is_child(obj: Object, parent: Object | None) -> bool:
    """Return True if obj is a member of parent."""
    if parent is None or isinstance(obj, Module) or isinstance(parent, Module):
        return True

    return obj.parent is parent


@cache
def get_object(name: str, module: str | None = None) -> Object | None:
    if not (fullname := get_fullname(name, module)):
        return None

    if obj := objects.get(fullname):
        return obj

    if not (name_module := split_name(fullname)):
        return None

    name_, module = name_module
    if not name_:
        return None

    if not module:
        return create_module(name_)

    create_module(module)
    return objects.get(fullname)


def get_fullname_from_object(name: str, obj: Object) -> str | None:
    """Return fullname from object."""
    if isinstance(obj, Module):
        return get_fullname(name, obj.name)

    if isinstance(obj, Parent):  # noqa: SIM102
        if child := obj.get(name):
            return child.fullname

    if "." not in name:
        if obj.parent:
            return get_fullname_from_object(name, obj.parent)

        return get_fullname(name, obj.module)

    parent, name_ = name.rsplit(".", maxsplit=1)

    if obj_ := objects.get(parent):
        return get_fullname_from_object(name, obj_)

    if obj.name == parent:
        return get_fullname_from_object(name_, obj)

    return get_fullname(name)


def get_members(
    obj: Parent,
    predicate: Callable[[Object], bool] | None = None,
) -> dict[str, Object]:
    members: dict[str, Object] = {}

    for name, child in obj.children.items():
        if name not in members and (not predicate or predicate(child)):
            members[name] = child

    module = obj.name if isinstance(obj, Module) else obj.module

    for name, node in parse(obj.node, module):
        if isinstance(node, mkapi.nodes.Object) and name not in members:
            child = get_object(node.name, node.module)
            if child and (not predicate or predicate(child)):
                members[name] = child

    return members
