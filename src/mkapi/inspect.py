"""inspect module."""
from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mkapi.ast
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

    name: str
    module: str
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
class Module:
    """Module class."""

    name: str
    node: ast.Module | None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


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
            yield Object(child.name, module, f"{module}.{child.name}", child)

        elif _is_assign(child) and (name := mkapi.ast.get_assign_name(child)):
            yield Assign(name, module, f"{module}.{name}", child)

        elif isinstance(child, ast.Import):
            for name, fullname in _iter_imports_from_import(child):
                yield Import(name, module, fullname, child)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                pass
                # yield from _iter_names_from_all(child, module)
            else:
                for name, fullname in _iter_imports_from_import_from(child, module):
                    yield Import(name, module, fullname, child)


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


def _iter_names_from_all(node: ast.ImportFrom, module: str) -> Iterator[Module | Object | Assign | Import]:
    module = _get_module_from_import_from(node, module)
    yield from get_members(module).values()


@cache
def get_members(module: str) -> dict[str, Module | Object | Assign | Import]:
    members = {}

    for member in _iter_names(module):
        if isinstance(member, Import) and (resolved := _resolve(member.fullname)):
            members[member.name] = resolved
        else:
            members[member.name] = member

    return members


@cache
def _resolve(fullname: str) -> Module | Object | Assign | Import | None:
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

        return _resolve(member.fullname)

    return None


def resolve(fullname: str) -> str | None:
    if resolved := _resolve(fullname):
        return resolved.name if isinstance(resolved, Module) else resolved.fullname

    return None


def resolve_with_attribute(fullname: str) -> str | None:
    """Resolve name with attribute."""
    if resolved := resolve(fullname):
        return resolved

    if "." in fullname:
        name, attr = fullname.rsplit(".", maxsplit=1)
        if resolved := resolve(name):
            return f"{resolved}.{attr}"

    return None


@cache
def get_member(name: str, module: str) -> Module | Object | Assign | Import | None:
    """Return an object in the module."""
    members = get_members(module)

    if name in members:
        return members[name]

    if "." not in name:
        return None

    name, attr = name.rsplit(".", maxsplit=1)
    if name in members and isinstance(members[name], Module):
        module = members[name].name
        return get_member(attr, module)

    return None


@cache
def get_fullname(name: str, module: str) -> str | None:
    """Return the fullname of an object in the module."""
    if name.startswith(module) or module.startswith(name):
        return name

    if member := get_member(name, module):
        return member.name if isinstance(member, Module) else member.fullname

    if "." not in name:
        return None

    name, attr = name.rsplit(".", maxsplit=1)
    if member := get_member(name, module):
        fullname = member.name if isinstance(member, Module) else member.fullname
        return f"{fullname}.{attr}"

    return None


@cache
def get_members_all(module: str) -> dict[str, Module | Object | Assign]:
    members = get_members(module)

    member_all = get_member("__all__", module)
    if not member_all:
        return {}

    members_all = {}
    node = member_all.node
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.List | ast.Tuple):
        for arg in node.value.elts:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):  # noqa: SIM102
                if arg.value in members:
                    members_all[arg.value] = members[arg.value]

    return members_all


@cache
def get_all_from_ast(module: str) -> dict[str, str]:
    """Return name dictonary of __all__ using ast."""
    names = {}

    for name, member in get_members_all(module).items():
        fullname = member.name if isinstance(member, Module) else member.fullname
        names[name] = fullname

    return names


@cache
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


@cache
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
