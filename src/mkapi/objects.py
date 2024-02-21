"""Object module."""
from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.ast import is_classmethod, is_function, is_property, is_staticmethod
from mkapi.utils import (
    cache,
    get_module_node,
    get_module_node_source,
    is_package,
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


@dataclass
class Node:
    name: str
    node: ast.AST

    def __repr__(self) -> str:
        kind = get_kind(self)
        return f"{kind.title()}({self.name!r})"


@dataclass(repr=False)
class Import(Node):
    node: ast.Import | ast.ImportFrom
    module: str
    fullname: str


objects: dict[tuple[str, str], Object] = cache({})


@dataclass(repr=False)
class Object(Node):
    qualname: str
    module: str
    doc: str | None

    def __post_init__(self):
        objects[(self.name, self.module)] = self


@dataclass(repr=False)
class Assign(Object):
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
    dict: dict[str, Module | Object | Import]

    def get(self, name) -> Module | Object | Import | None:
        return self.dict.get(name)


@dataclass(repr=False)
class Class(Callable):
    node: ast.ClassDef


@dataclass(repr=False)
class Function(Callable):
    node: ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Module(Node):
    node: ast.Module | None
    doc: str | None
    dict: dict[str, Module | Object | Import] | None
    source: str

    def get(self, name) -> Module | Object | Import | None:
        if not self.dict:
            return None

        return self.dict.get(name)


def _iter_nodes(
    node: ast.AST,
    module: str,
    parent: str | None = None,
) -> Iterator[Module | Object | Import]:
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            yield create_class(child, module, parent)

        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            if is_function(child):
                yield create_function(child, module, parent)
            elif is_property(child):
                yield create_property(child, module, parent)

        elif isinstance(child, ast.AnnAssign | ast.Assign | TypeAlias):
            if name := mkapi.ast.get_assign_name(child):
                yield create_assign(name, child, module, parent)

        elif isinstance(child, ast.Import):
            for name, fullname in _iter_imports_from_import(child):
                yield Import(name, child, module, fullname)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                yield from _iter_members_from_star(child, module, parent)

            else:
                it = _iter_imports_from_import_from(child, module)
                for name, fullname in it:
                    yield Import(name, child, module, fullname)


def _iter_imports_from_import(node: ast.Import) -> Iterator[tuple[str, str]]:
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name

        else:
            for module_name in iter_parent_module_names(alias.name):
                yield module_name, module_name


def _get_module_from_import_from(node: ast.ImportFrom, module: str) -> str:
    if not node.module:
        return module

    if not node.level:
        return node.module

    names = module.split(".")

    if is_package(module):  # noqa: SIM108
        prefix = ".".join(names[: len(names) - node.level + 1])

    else:
        prefix = ".".join(names[: -node.level])

    return f"{prefix}.{node.module}"


def _iter_imports_from_import_from(
    node: ast.ImportFrom,
    module: str,
) -> Iterator[tuple[str, str]]:
    module = _get_module_from_import_from(node, module)
    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _iter_members_from_star(
    node: ast.ImportFrom,
    module: str,
    parent: str | None,
) -> Iterator[Module | Object | Import]:
    module = _get_module_from_import_from(node, module)
    if node_ := get_module_node(module):
        yield from _iter_nodes(node_, module, parent)


def create_class(node: ast.ClassDef, module: str, parent: str | None) -> Class:
    name = node.name
    qualname = f"{parent}.{name}" if parent else name
    doc = ast.get_docstring(node)

    dict_ = _get_members(node, module, qualname)

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


def iter_base_classes(name: str, module: str) -> Iterator[Class]:
    for basename, basemodule in _iter_base_classes(name, module):
        if cls := objects.get((basename, basemodule)):
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
            if (assign := cls.get(param.name)) and isinstance(assign, Assign):
                args = (assign.name, assign.type, assign.default)
                yield Parameter(*args, param.kind)

            else:
                raise NotImplementedError


@cache
def get_base_classes(name: str, module: str) -> list[Class]:
    return list(iter_base_classes(name, module))


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

    dict_ = _get_members(node, module, qualname)

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


def create_assign(
    name: str,
    node: ast.AnnAssign | ast.Assign | TypeAlias,  # type: ignore
    module: str,
    parent: str | None,
) -> Assign:
    qualname = f"{parent}.{name}" if parent else name
    doc = node.__doc__

    type_ = mkapi.ast.get_assign_type(node)
    default = None if TypeAlias and isinstance(node, TypeAlias) else node.value

    return Assign(name, node, qualname, module, doc, type_, default)


def _create_module(name: str, node: ast.Module, source: str) -> Module:
    doc = ast.get_docstring(node)
    dict_ = _get_members(node, name, None)

    return Module(name, node, doc, dict_, source)


@cache
def create_module(name: str) -> Module | None:
    if not (node_source := get_module_node_source(name)):
        return None

    return _create_module(name, *node_source)


def _get_members(
    node: ast.AST,
    module: str,
    parent: str | None,
) -> dict[str, Module | Object | Import]:
    members: dict[str, Module | Object | Import] = {}

    for member in _iter_nodes(node, module, parent):
        name = member.name

        if isinstance(node, ast.Module) and isinstance(member, Import):
            resolved = _resolve(member.fullname, parent)
            members[name] = resolved or member

        else:
            members[name] = member

    return members


@cache
def _resolve(
    fullname: str,
    parent: str | None = None,
) -> Module | Object | Import | None:
    """Resolve name."""
    if node_source := get_module_node_source(fullname):
        node, source = node_source
        return Module(fullname, node, None, None, source)

    if "." not in fullname:
        return None

    module, name = fullname.rsplit(".", maxsplit=1)

    if not (node := get_module_node(module)):
        return None

    for member in _iter_nodes(node, module, parent):
        if member.name == name:
            if not isinstance(member, Import):
                return member

            if member.fullname == fullname:
                return None

            return _resolve(member.fullname, parent)

    return None


def walk(obj: Module | Class | Function) -> Iterator[Module | Object | Import]:
    yield obj

    members = obj.dict or {}

    for member in members.values():
        if isinstance(member, Module | Class | Function):
            yield from walk(member)
        else:
            yield member


def _add_doc_comment(assigns: Iterable[Assign], source: str) -> None:
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


@cache
def load_module(name: str) -> Module | None:
    if not (module := create_module(name)):
        return None

    it = (child for child in walk(module) if isinstance(child, Assign))
    _add_doc_comment(it, module.source)

    return module


@cache
def get_members(module: str) -> dict[str, Module | Object | Import]:
    if node := get_module_node(module):
        return _get_members(node, module, None)

    return {}


@cache
def get_members_all(module: str) -> dict[str, Node]:
    members = importlib.import_module(module).__dict__
    if not (names := members.get("__all__")):
        return {}

    members = get_members(module)
    members_all = {}

    for name in names:
        if member := members.get(name):
            members_all[name] = member

    return members_all


@cache
def get_member(name: str, module: str) -> Module | Object | Import | None:
    """Return an object in the module."""
    members = get_members(module)

    if member := members.get(name):
        return member

    if "." not in name:
        return None

    module, name = name.rsplit(".", maxsplit=1)

    if (member := members.get(module)) and isinstance(member, Module):
        return get_member(name, member.name)

    return None


@cache
def resolve(fullname: str) -> str | None:
    if resolved := _resolve(fullname):
        if isinstance(resolved, Class | Function | Assign):
            return f"{resolved.module}.{resolved.name}"

        if isinstance(resolved, Import):
            return resolved.fullname

        return resolved.name

    if "." not in fullname:
        return None

    fullname, attr = fullname.rsplit(".", maxsplit=1)

    if resolved := resolve(fullname):
        return f"{resolved}.{attr}"

    return None


@cache
def get_fullname(name: str, module: str) -> str | None:
    """Return the fullname of an object in the module."""
    if name.startswith(module) or module.startswith(name):
        return name

    return resolve(f"{module}.{name}")


def iter_decorator_names(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
) -> Iterator[str]:
    """Yield decorator_names."""
    for deco in node.decorator_list:
        deco_name = next(mkapi.ast.iter_identifiers(deco))

        if name := get_fullname(deco_name, module):
            yield name

        else:
            yield deco_name


def has_decorator(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    module: str,
) -> bool:
    """Return a decorator expr by name."""
    it = iter_decorator_names(node, module)
    return any(deco_name == name for deco_name in it)


def is_dataclass(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
) -> bool:
    """Return True if the [Class] instance is a dataclass."""
    return has_decorator(node, "dataclasses.dataclass", module)


@cache
def _get_module_name(module: str) -> str | None:
    try:
        return importlib.import_module(module).__name__
    except ModuleNotFoundError:
        return


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


def is_method(func: Function) -> bool:
    return "." in func.qualname


def _get_kind_function(func: Function) -> str:
    if is_classmethod(func.node):
        return "classmethod"

    if is_staticmethod(func.node):
        return "staticmethod"

    return "method" if is_method(func) else "function"


def get_kind(obj: Node) -> str:
    """Return kind."""
    if isinstance(obj, Module):
        return "package" if is_package(obj.name) else "module"

    # if isinstance(obj, Class):
    #     return "dataclass" if mkapi.inspect.is_dataclass(obj) else "class"

    if isinstance(obj, Function):
        return _get_kind_function(obj)

    # if isinstance(obj, Attribute):
    #     return "property" if isinstance(obj.node, ast.FunctionDef) else "attribute"

    return obj.__class__.__name__.lower()


# def is_empty(obj: Object) -> bool:
#     """Return True if a [Object] instance is empty."""
#     if isinstance(obj, Attribute) and not obj.doc.sections:
#         return True

#     if not docstrings.is_empty(obj.doc):
#         return False

#     if isinstance(obj, Function) and obj.name.str.startswith("_"):
#         return True
