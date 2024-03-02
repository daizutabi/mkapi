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
from mkapi.nodes import parse, resolve_from_module
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
    from collections.abc import Iterator

    from mkapi.docs import Doc


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
        self.qualname = f"{self.parent.qualname}.{self.name}" if self.parent else self.name
        self.fullname = f"{self.module}.{self.qualname}" if self.module else self.name

        types = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        node = self.node
        text = ast.get_docstring(node) if isinstance(node, types) else node.__doc__
        self.doc = create_doc(text)

        objects[self.fullname] = self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


objects: dict[str, Object] = cache({})


def iter_child_objects(node: AST, module: str, parent: Parent | None) -> Iterator[Object]:
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
class Callable(Parent):
    parameters: list[Parameter]
    raises: list[ast.expr]

    def __post_init__(self):
        super().__post_init__()

        for obj in iter_child_objects(self.node, self.module, self):
            self.children[obj.name] = obj


@dataclass(repr=False)
class Class(Callable):
    node: ast.ClassDef


@dataclass(repr=False)
class Function(Callable):
    node: ast.FunctionDef | ast.AsyncFunctionDef


def create_class(node: ast.ClassDef, module: str, parent: Parent | None) -> Class:
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

            if doc := _get_doc_from_comment(attr.node, lines):
                attr.doc = doc

    return module


def _get_doc_from_comment(node: AST, lines: list[str]) -> Doc | None:
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
def resolve(fullname: str) -> tuple[str | None, str | None] | None:
    if not (name_module := split_name(fullname)):
        return None

    name, module = name_module
    if not module:
        return name, None

    if name_module := split_name(name):
        return resolve(name)

    names = name.split(".")
    node = get_module_node(module)

    for name, obj in parse(node, module):
        if name == names[0]:
            if isinstance(obj, mkapi.nodes.Object):
                qualname = ".".join([obj.name, *names[1:]])
                return qualname, obj.module
            if isinstance(obj, mkapi.nodes.Import):
                return None, obj.fullname

    return None


@cache
def get_object(fullname: str) -> Object | None:
    if obj := objects.get(fullname):
        return obj

    if not (name_module := resolve(fullname)):
        return None

    name, module = name_module
    if not name:
        return None

    if not module:
        return create_module(name)

    create_module(module)
    return objects.get(f"{module}.{name}")


def resolve_from_object(name: str, obj: Object) -> str | None:
    """Return fullname from object."""
    if isinstance(obj, Module):
        return resolve_from_module(name, obj.name)

    if isinstance(obj, Parent):  # noqa: SIM102
        if child := obj.get(name):
            return child.fullname

    if "." not in name:
        if obj.parent:
            return resolve_from_object(name, obj.parent)

        return resolve_from_module(name, obj.module)

    parent, name_ = name.rsplit(".", maxsplit=1)

    if obj_ := objects.get(parent):
        return resolve_from_object(name, obj_)

    if obj.name == parent:
        return resolve_from_object(name_, obj)

    if not (name_module := resolve(name)):
        return None

    name_, module = name_module

    if not module:
        return name_

    if not name_:
        return module

    return f"{module}.{name_}"


# def iter_child_objects(
#     obj: Parent,
#     predicate: Callable_[[Object, Object | None], bool] | None = None,
# ) -> Iterator[tuple[str, Object]]:
#     """Yield child [Object] instances."""
#     for name, child in obj.children.items():
#         if not predicate or predicate(child, obj):
#             yield name, child
#             if isinstance(child,Pa)
#             yield from iter_objects_with_depth(child, maxdepth, predicate, depth + 1)


# def iter_objects(
#     obj: Object,
#     maxdepth: int = -1,
#     predicate: Callable_[[Object, Object | None], bool] | None = None,
# ) -> Iterator[Object]:
#     """Yield [Object] instances."""
#     for child, _ in iter_objects_with_depth(obj, maxdepth, predicate, 0):
#         yield child
