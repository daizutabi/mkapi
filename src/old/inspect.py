"""inspect module."""
from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.utils import (
    cache,
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
class Member:
    """Node class."""

    name: str
    module: str
    node: ast.AST

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        return f"{cls_name}({self.module}.{self.name})"


@dataclass(repr=False)
class Object(Member):
    """Object class."""

    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Assign(Member):
    """Assign class."""

    node: ast.AnnAssign | ast.Assign | TypeAlias  # type: ignore


@dataclass(repr=False)
class Import(Member):
    """Import class."""

    node: ast.Import | ast.ImportFrom
    fullname: str


@dataclass(repr=False)
class Module:
    """Module class."""

    name: str
    node: ast.Module | None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


# For Python <= 3.11
def _is_assign(node: ast.AST) -> bool:
    if isinstance(node, ast.AnnAssign | ast.Assign):
        return True

    if TypeAlias and isinstance(node, TypeAlias):
        return True

    return False


def _iter_members(module: str) -> Iterator[Module | Object | Assign | Import]:
    if not (node := get_module_node(module)):
        return

    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            yield Object(child.name, module, child)

        elif _is_assign(child) and (name := mkapi.ast.get_assign_name(child)):
            yield Assign(name, module, child)

        elif isinstance(child, ast.Import):
            for name, fullname in _iter_imports_from_import(child):
                yield Import(name, module, child, fullname)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                yield from _iter_members_from_star(child, module)
            else:
                for name, fullname in _iter_imports_from_import_from(child, module):
                    yield Import(name, module, child, fullname)


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


def _iter_imports_from_import_from(node: ast.ImportFrom, module: str) -> Iterator[tuple[str, str]]:
    module = _get_module_from_import_from(node, module)
    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _iter_members_from_star(node: ast.ImportFrom, module: str) -> Iterator[Module | Object | Assign]:
    module = _get_module_from_import_from(node, module)
    yield from get_members(module).values()


@cache
def get_members(module: str) -> dict[str, Module | Object | Assign]:
    members = {}

    for member in _iter_members(module):
        name = member.name

        if isinstance(member, Module | Object | Assign):
            members[name] = member

        elif resolved := _resolve(member.fullname):
            members[name] = resolved

    return members


@cache
def _resolve(fullname: str) -> Module | Object | Assign | None:
    """Resolve name."""

    if node := get_module_node(fullname):
        return Module(fullname, node)

    if "." not in fullname:
        return Module(fullname, None)

    module, name = fullname.rsplit(".", maxsplit=1)

    for member in _iter_members(module):
        if member.name == name:
            if isinstance(member, Module | Object | Assign):
                return member

            if member.fullname == fullname:
                return None

            return _resolve(member.fullname)

    return None


def _get_module_name(name: str) -> str:
    return importlib.import_module(name).__name__


@cache
def resolve(fullname: str) -> str | None:
    if resolved := _resolve(fullname):
        if isinstance(resolved, Module):
            return _get_module_name(resolved.name)

        module = _get_module_name(resolved.module)
        return f"{module}.{resolved.name}"

    if "." not in fullname:
        return None

    fullname, attr = fullname.rsplit(".", maxsplit=1)

    if resolved := resolve(fullname):
        return f"{resolved}.{attr}"

    return None


@cache
def get_members_all(module: str) -> dict[str, Module | Object | Assign]:
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
def get_member(name: str, module: str) -> Module | Object | Assign | None:
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
def get_fullname(name: str, module: str) -> str | None:
    """Return the fullname of an object in the module."""
    if name.startswith(module) or module.startswith(name):
        return name

    if member := get_member(name, module):
        if isinstance(member, Module):
            return _get_module_name(member.name)

        module = _get_module_name(member.module)
        return f"{module}.{member.name}"

    return None


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

# def _iter_names_all_ast(module: str) -> Iterator[str]:
#     if not (all_ := get_member("__all__", module)):
#         return

#     node = all_.node
#     if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.List | ast.Tuple):
#         return

#     for arg in node.value.elts:
#         if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
#             yield arg.value
