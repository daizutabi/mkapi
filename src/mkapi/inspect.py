"""inspect module."""
from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.globals import get_fullname
from mkapi.utils import (
    cache,
    get_by_name,
    get_module_node,
    is_package,
    iter_parent_module_names,
)

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from collections.abc import Iterator

    from mkapi.objects import Class, Function


@dataclass(repr=False)
class Name:
    """Name class."""

    module: str
    name: str
    fullname: str
    node: ast.AST

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.fullname})"


@dataclass(repr=False)
class Object(Name):
    """Object class."""

    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Assign(Name):
    """Assign class."""

    node: ast.AnnAssign | ast.Assign | TypeAlias  # type: ignore


@dataclass(repr=False)
class Import(Name):
    """Import class."""

    node: ast.Import | ast.ImportFrom


@dataclass(repr=False)
class Module(Name):
    """Module class."""

    node: ast.Module | None
    module: str = field(init=False)
    fullname: str = field(init=False)

    def __post_init__(self):
        self.module = self.fullname = self.name


def _is_assign(node: ast.AST) -> bool:
    if isinstance(node, ast.AnnAssign | ast.Assign):
        return True

    if TypeAlias and isinstance(node, TypeAlias):
        return True

    return False


def _iter_names(module: str) -> Iterator[Module | Object | Assign | Import]:
    if not (node := get_module_node(module)):
        return

    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            yield Object(module, child.name, f"{module}.{child.name}", child)

        elif _is_assign(child) and (name := mkapi.ast.get_assign_name(child)):
            yield Assign(module, name, f"{module}.{name}", child)

        elif isinstance(child, ast.Import):
            for name, fullname in _iter_imports_from_import(child):
                yield Import(module, name, fullname, child)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                yield from _iter_names_from_all(child, module)
            else:
                for name, fullname in _iter_imports_from_import_from(child, module):
                    yield Import(module, name, fullname, child)


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

    if node.level:
        names = module.split(".")

        if is_package(module):  # noqa: SIM108
            prefix = ".".join(names[: len(names) - node.level + 1])

        else:
            prefix = ".".join(names[: -node.level])

        return f"{prefix}.{node.module}"

    return node.module


def _iter_imports_from_import_from(node: ast.ImportFrom, module: str) -> Iterator[tuple[str, str]]:
    module = _get_module_from_import_from(node, module)
    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _iter_names_from_all(node: ast.ImportFrom, module: str) -> Iterator[Module | Object | Assign]:
    module = _get_module_from_import_from(node, module)
    yield from get_members(module).values()


@cache
def get_members(module: str) -> dict[str, Module | Object | Assign]:
    members = {}

    for member in _iter_names(module):
        if isinstance(member, Module | Object | Assign):
            members[member.name] = member

        elif resolved := resolve(member.fullname):
            members[member.name] = resolved

    return members


@cache
def resolve(fullname: str) -> Module | Object | Assign | None:
    """Resolve name."""
    if node := get_module_node(fullname):
        return Module(fullname, node)

    if "." not in fullname:
        return Module(fullname, None)

    module, name = fullname.rsplit(".", maxsplit=1)

    if member := get_by_name(_iter_names(module), name):
        if isinstance(member, Module | Object | Assign):
            return member

        if member.fullname == fullname:
            return None

        return resolve(member.fullname)

    return None


# def resolve_with_attribute(name: str) -> str | None:
#     """Resolve name with attribute."""
#     if fullname := resolve(name):
#         return fullname

#     if "." in name:
#         name_, attr = name.rsplit(".", maxsplit=1)
#         if fullname := resolve(name_):
#             return f"{fullname}.{attr}"

#     return None


# def _iter_globals(module: str) -> Iterator[Object | Import]:
#     n = len(module) + 1
#     for name in _iter_objects(module):
#         yield Object(name[n:], name)
#     for import_ in _iter_imports(module):
#         name = import_.name[n:]
#         if fullname := resolve(import_.fullname):
#             yield Import(name, fullname)
#         else:
#             yield Import(name, import_.fullname)


# @cache
# def get_globals(module: str) -> list[Object | Import]:
#     """Return a global list of a module."""
#     return list(_iter_globals(module))


# @cache
# def get_fullname(name: str, module: str) -> str | None:
#     """Return the fullname of an object in the module."""
#     if name.startswith(module) or module.startswith(name):
#         return name
#     names = get_globals(module)
#     if global_ := get_by_name(names, name):
#         return global_.fullname
#     if "." not in name:
#         return None
#     name_, attr = name.rsplit(".", maxsplit=1)
#     global_ = get_by_name(names, name_)
#     if isinstance(global_, Object):
#         return f"{global_.fullname}.{attr}"
#     if isinstance(global_, Import):
#         return resolve(f"{global_.fullname}.{attr}")
#     return name


def _iter_all(node: ast.AST) -> Iterator[str]:
    if isinstance(node, ast.Assign):  # noqa: SIM102
        if mkapi.ast.get_assign_name(node) == "__all__":  # noqa: SIM102
            if isinstance(node.value, ast.List | ast.Tuple):
                for arg in node.value.elts:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        yield arg.value


def _iter_objects_from_all(module: str) -> Iterator[str]:
    if not (node := get_module_node(module)):
        return
    for child in ast.iter_child_nodes(node):
        if names := list(_iter_all(child)):
            for name in names:
                yield f"{module}.{name}"
            return


def get_all_from_ast(module: str) -> dict[str, str]:
    """Return name dictonary of __all__ using ast."""
    names = {}
    n = len(module) + 1

    for name in _iter_objects_from_all(module):
        if fullname := resolve(name):
            names[name[n:]] = fullname

    return names


def get_all_from_importlib(module: str) -> dict[str, str]:
    """Return name dictonary of __all__ using importlib."""
    try:
        module_type = importlib.import_module(module)
    except ModuleNotFoundError:
        return {}

    members = getattr(module_type, "__dict__", {})  # Must use __dict__.
    if not isinstance(members, dict) or "__all__" not in members:
        return {}

    names = {}
    for name in members["__all__"]:
        obj = members.get(name)
        if obj is None:
            continue
        if inspect.ismodule(obj):
            names[name] = obj.__name__
        elif not (modulename := getattr(obj, "__module__", None)):
            continue
        elif qualname := getattr(obj, "__qualname__", None):
            names[name] = f"{modulename}.{qualname}"

    return names


def get_all(module: str) -> dict[str, str]:
    """Return name dictonary of __all__."""
    all_from_ast = get_all_from_ast(module)
    all_from_importlib = get_all_from_importlib(module)
    all_from_ast.update(all_from_importlib)
    return all_from_ast


def iter_decorator_names(obj: Class | Function) -> Iterator[str]:
    """Yield decorator_names."""
    for deco in obj.node.decorator_list:
        deco_name = next(mkapi.ast.iter_identifiers(deco))

        if name := get_fullname(deco_name, obj.module.name.str):
            yield name

        else:
            yield deco_name


def get_decorator(obj: Class | Function, name: str) -> ast.expr | None:
    """Return a decorator expr by name."""
    for deco in obj.node.decorator_list:
        deco_name = next(mkapi.ast.iter_identifiers(deco))

        if get_fullname(deco_name, obj.module.name.str) == name:
            return deco

        if deco_name == name:
            return deco

    return None


def is_dataclass(cls: Class) -> bool:
    """Return True if the [Class] instance is a dataclass."""
    return get_decorator(cls, "dataclasses.dataclass") is not None


def is_classmethod(func: Function) -> bool:
    """Return True if the [Function] instance is a classmethod."""
    return get_decorator(func, "classmethod") is not None


def is_staticmethod(func: Function) -> bool:
    """Return True if the [Function] instance is a staticmethod."""
    return get_decorator(func, "staticmethod") is not None


# def _iter_decorator_args(deco: ast.expr) -> Iterator[tuple[str, Any]]:
#     for child in ast.iter_child_nodes(deco):
#         if isinstance(child, ast.keyword):
#             if child.arg and isinstance(child.value, ast.Constant):
#                 yield child.arg, child.value.value


# def _get_decorator_args(deco: ast.expr) -> dict[str, Any]:
#     return dict(_iter_decorator_args(deco))
