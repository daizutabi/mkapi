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
    is_classmethod,
    is_function,
    is_property,
    is_staticmethod,
)
from mkapi.docs import create_doc, create_doc_comment, is_empty, split_type
from mkapi.nodes import _parse, is_dataclass, resolve, resolve_from_module
from mkapi.utils import (
    cache,
    get_module_name,
    get_module_node,
    get_module_node_source,
    get_module_source,
    is_package,
    iter_attribute_names,
    iter_identifiers,
)

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Callable as Callable_
    from collections.abc import Iterator
    from inspect import _ParameterKind

    from mkapi.docs import Doc


@dataclass
class Parameter:
    name: str
    type: ast.expr | None
    default: ast.expr | None
    kind: _ParameterKind

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


def iter_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[Parameter]:
    for name, type_, default, kind in mkapi.ast.iter_parameters(node):
        yield Parameter(name, type_, default, kind)


objects: dict[str, Object] = cache({})
aliases: dict[str, list[str]] = cache({})


def _register_object(fullname: str, obj: Object):
    objects[fullname] = obj

    aliases.setdefault(obj.fullname, [])

    if fullname not in aliases[obj.fullname]:
        aliases[obj.fullname].append(fullname)


def _create_doc(node: AST) -> Doc:
    if isinstance(
        node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module
    ):
        text = ast.get_docstring(node)
    else:
        text = node.__doc__

    return create_doc(text)


@dataclass
class Object:
    name: str
    node: AST
    module: str
    parent: Parent | None
    doc: Doc = field(init=False)
    kind: str = field(init=False)

    def __post_init__(self):
        self.doc = _create_doc(self.node)
        self.kind = get_kind(self)
        _register_object(self.fullname, self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"

    @property
    def qualname(self) -> str:
        return f"{self.parent.qualname}.{self.name}" if self.parent else self.name

    @property
    def fullname(self) -> str:
        return get_fullname(self)


def _create_object(node: AST, module: str, parent: Parent | None) -> Object | None:
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


def _iter_child_objects(node: AST, module: str, parent: Parent) -> Iterator[Object]:
    for child in mkapi.ast.iter_child_nodes(node):
        if obj := _create_object(child, module, parent):
            yield obj


@dataclass(repr=False)
class Type(Object):
    type: ast.expr | None

    def __post_init__(self):
        super().__post_init__()
        split_type(self.doc)


@dataclass(repr=False)
class Attribute(Type):
    node: ast.AnnAssign | ast.Assign | TypeAlias  # type: ignore
    default: ast.expr | None


@dataclass(repr=False)
class Property(Type):
    node: ast.FunctionDef | ast.AsyncFunctionDef


T = TypeVar("T")


@dataclass(repr=False)
class Parent(Object):
    children: dict[str, Object] = field(default_factory=dict, init=False)

    def set_children(self, children: dict[str, Object]):
        self.children = children

        for name, child in self.objects():
            _register_object(f"{self.fullname}.{name}", child)

    def get(self, name: str, type_: type[T] = Object) -> T | None:
        child = self.children.get(name)

        return child if isinstance(child, type_) else None

    def objects(self, type_: type[T] = Object) -> list[tuple[str, T]]:
        it = self.children.items()

        return [(name, obj) for (name, obj) in it if isinstance(obj, type_)]

    def iter_objects(self, type_: type[T] = Object) -> Iterator[T]:
        for obj in self.children.values():
            if isinstance(obj, type_):
                yield obj

            if isinstance(obj, Parent):
                yield from obj.iter_objects(type_)


@dataclass(repr=False)
class Callable(Parent):
    parameters: list[Parameter]
    raises: list[ast.expr]


@dataclass(repr=False)
class Class(Callable):
    node: ast.ClassDef


@dataclass(repr=False)
class Function(Callable):
    node: ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Module(Parent):
    node: ast.Module


def create_class(node: ast.ClassDef, module: str, parent: Parent | None) -> Class:
    cls = Class(node.name, node, module, parent, [], [])

    children = {obj.name: obj for obj in _iter_child_objects(node, module, cls)}

    if (func := children.get("__init__")) and isinstance(func, Function):
        for name, obj in iter_attributes_from_function(func, cls):
            children.setdefault(name, obj)

    for base in get_base_classes(node.name, module):
        for name, obj in base.objects():
            children.setdefault(name, obj)

    cls.set_children(children)

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


def iter_attributes_from_function(
    func: Function,
    parent: Parent,
) -> Iterator[tuple[str, Attribute]]:
    self = func.parameters[0].name

    for name, obj in func.objects(Attribute):
        if name.startswith(f"{self}."):
            name_ = name[len(self) + 1 :]
            attr = create_attribute(name_, obj.node, obj.module, parent)
            yield name_, attr
            del func.children[name]


def iter_dataclass_parameters(cls: Class) -> Iterator[Parameter]:
    obj = mkapi.utils.get_object(cls.name, cls.module)

    if inspect.isclass(obj):
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
    parent: Parent | None,
) -> Function:
    params = list(iter_parameters(node))
    raises = list(mkapi.ast.iter_raises(node))

    func = Function(node.name, node, module, parent, params, raises)

    children = {obj.name: obj for obj in _iter_child_objects(node, module, func)}
    func.set_children(children)

    return func


def create_property(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    parent: Parent | None,
) -> Property:
    return Property(node.name, node, module, parent, node.returns)


def create_attribute(
    name: str,
    node: ast.AnnAssign | ast.Assign | TypeAlias,  # type: ignore
    module: str,
    parent: Parent | None,
) -> Attribute:
    type_ = mkapi.ast.get_assign_type(node)
    default = None if TypeAlias and isinstance(node, TypeAlias) else node.value

    return Attribute(name, node, module, parent, type_, default)


def _create_module(name: str, node: ast.Module, source: str | None = None) -> Module:
    module = Module(name, node, name, None)

    children: dict[str, Object] = {}

    for name_, child in _parse(node, name):
        if isinstance(child, mkapi.nodes.Module):
            children[name_] = Module(child.name, child.node, child.name, None)

        elif obj := _create_object(child.node, child.module, None):
            children[name_] = obj

    module.set_children(children)

    if source:
        lines = source.splitlines()
        for attr in module.iter_objects(Attribute):
            if not is_empty(attr.doc) or attr.module != name:
                continue

            if doc := _get_doc_from_comment(attr.node, lines):
                attr.doc = doc

    return module


def _get_doc_from_comment(node: ast.AST, lines: list[str]) -> Doc | None:
    line = lines[node.lineno - 1][node.end_col_offset :].strip()

    if line.startswith("#:"):
        return create_doc_comment(line[2:].strip())

    if node.lineno > 1:
        line = lines[node.lineno - 2][node.col_offset :]
        if line.startswith("#:"):
            return create_doc_comment(line[2:].strip())

    return None


@cache
def create_module(name: str) -> Module | None:
    if not (node_source := get_module_node_source(name)):
        return None

    return _create_module(name, *node_source)


def _iter_base_classes(name: str, module: str) -> Iterator[tuple[str, str]]:
    if not module:
        return

    obj = mkapi.utils.get_object(name, module)
    if inspect.isclass(obj):
        for base in obj.__bases__:
            if base.__module__ != "builtins":
                basename = next(iter_identifiers(base.__name__))[0]
                yield basename, base.__module__


@cache
def get_object(fullname: str) -> Object | None:
    if fullname in objects:
        return objects[fullname]

    for module in iter_attribute_names(fullname):
        if create_module(module) and fullname in objects:
            return objects[fullname]

    return None


def _resolve_from_object(name: str, obj: Object) -> str | None:
    """Return fullname from object."""
    if isinstance(obj, Parent):  # noqa: SIM102
        if child := obj.get(name):
            return get_fullname(child)

    if isinstance(obj, Module):
        return resolve_from_module(name, obj.name)

    if "." not in name:
        return resolve_from_module(name, obj.module)

    parent, name_ = name.rsplit(".", maxsplit=1)

    if obj_ := objects.get(parent):
        return _resolve_from_object(name, obj_)

    if obj.name == parent:
        return _resolve_from_object(name_, obj)

    return resolve(name)


@cache
def resolve_from_object(name: str, fullname: str) -> str | None:
    """Return fullname from object."""
    if obj := get_object(fullname):
        return _resolve_from_object(name, obj)

    return None


def get_fullname(obj: Object) -> str:
    if isinstance(obj, Module):
        return get_module_name(obj.name)

    module = get_module_name(obj.module)
    return f"{module}.{obj.qualname}"


def get_kind(obj: Object | Module) -> str:
    """Return kind."""
    if isinstance(obj, Module):
        return "package" if is_package(obj.name) else "module"

    if isinstance(obj, Class):
        return "dataclass" if is_dataclass(obj.node, obj.module) else "class"

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


def is_member(obj: Object, parent: Object | None) -> bool:
    """Return True if obj is a member of parent."""
    if parent is None:
        return True

    if isinstance(obj, Module) or isinstance(parent, Module):
        return True

    return obj.fullname.startswith(parent.fullname)


def iter_objects_with_depth(
    obj: Object,
    maxdepth: int = -1,
    predicate: Callable_[[Object, Object | None], bool] | None = None,
    depth: int = 0,
) -> Iterator[tuple[Object, int]]:
    """Yield [Object] instances and depth."""
    if not predicate or predicate(obj, None):
        yield obj, depth

    if depth == maxdepth or not isinstance(obj, Parent):
        return

    for name, child in obj.children.items():
        if not predicate or predicate(child, obj):
            yield from iter_objects_with_depth(child, maxdepth, predicate, depth + 1)


def iter_objects(
    obj: Object,
    maxdepth: int = -1,
    predicate: Callable_[[Object, Object | None], bool] | None = None,
) -> Iterator[Object]:
    """Yield [Object] instances."""
    for child, _ in iter_objects_with_depth(obj, maxdepth, predicate, 0):
        yield child
