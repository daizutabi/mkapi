"""Node module."""
from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.utils import (
    cache,
    get_module_name,
    get_module_node,
    is_package,
    iter_attribute_names,
)

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class Node:
    name: str
    node: ast.AST


@dataclass(repr=False)
class Import(Node):
    node: ast.Import | ast.ImportFrom
    module: str
    fullname: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.fullname!r})"


@dataclass(repr=False)
class Object(Node):
    module: str

    def __repr__(self) -> str:
        fullname = f"{self.module}.{self.name}"
        return f"{self.__class__.__name__}({fullname!r})"


@dataclass(repr=False)
class Module(Node):
    node: ast.Module

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


def _iter_nodes(node: ast.AST, module: str) -> Iterator[Object | Import]:
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.Import):
            for name, fullname in _iter_imports_from_import(child):
                yield Import(name, child, module, fullname)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                yield from _iter_members_from_star(child, module)

            else:
                it = _iter_imports_from_import_from(child, module)
                for name, fullname in it:
                    yield Import(name, child, module, fullname)

        elif isinstance(child, ast.AnnAssign | ast.Assign | TypeAlias):
            if name := mkapi.ast.get_assign_name(child):
                yield Object(name, child, module)

        elif isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            yield Object(child.name, child, module)


def _iter_imports_from_import(node: ast.Import) -> Iterator[tuple[str, str]]:
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name

        else:
            for module_name in iter_attribute_names(alias.name):
                yield module_name, module_name


def _get_module_from_import_from(node: ast.ImportFrom, module: str) -> str:
    if not node.module:
        return module

    if not node.level:
        return node.module

    names = module.split(".")

    if is_package(module):
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
) -> Iterator[Object | Import]:
    module = _get_module_from_import_from(node, module)
    if node_ := get_module_node(module):
        yield from _iter_nodes(node_, module)


def _resolve(fullname: str) -> Iterator[Module | Object | Import]:
    if node := get_module_node(fullname):
        yield Module(fullname, node)
        return

    if "." not in fullname:
        return

    module, name = fullname.rsplit(".", maxsplit=1)

    if not (node := get_module_node(module)):
        return

    for member in _iter_nodes(node, module):
        if member.name == name:
            if not isinstance(member, Import):
                yield member
                continue

            elif member.fullname == fullname:
                continue

            yield from _resolve(member.fullname)


def _parse(node: ast.Module, module: str) -> list[tuple[str, Module | Object | Import]]:
    members = []

    for member in _iter_nodes(node, module):
        name = member.name

        if isinstance(member, Import):
            if resolved := list(_resolve(member.fullname)):
                members.extend((name, x) for x in resolved)
            else:
                members.append((name, member))

        else:
            members.append((name, member))

    return members


@cache
def parse(module: str) -> list[tuple[str, Module | Object | Import]]:
    if node := get_module_node(module):
        return _parse(node, module)

    return []


def get_all_names(module: str) -> list[str]:
    members = importlib.import_module(module).__dict__

    members_all = members.get("__all__")
    if isinstance(members_all, list | tuple):
        return list(members_all)

    return []


def _split_fullname(obj: Module | Object | Import) -> tuple[str, str | None]:
    if isinstance(obj, Module):
        return get_module_name(obj.name), None

    if isinstance(obj, Object):
        module = get_module_name(obj.module)
        return module, obj.name

    return obj.fullname, None  # import


def _get_fullname(obj: Module | Object | Import) -> str:
    module, name = _split_fullname(obj)
    if name is None:
        return module

    return f"{module}.{name}"


def resolve_module_name(name: str) -> tuple[str, str | None] | None:
    if resolved := list(_resolve(name)):
        return _split_fullname(resolved[0])

    if "." not in name:
        return None

    name, attr = name.rsplit(".", maxsplit=1)

    if resolved := resolve_module_name(name):
        module, name_ = resolved
        name = f"{name_}.{attr}" if name_ else attr
        return module, name

    return None


def resolve(name: str) -> str | None:
    if module_name := resolve_module_name(name):
        module, name_ = module_name
        if name_ is None:
            return module

        return f"{module}.{name_}"

    return None


def resolve_from_module(name: str, module: str) -> str | None:
    if name.startswith(module) or module.startswith(name):
        return name

    for name_, obj in parse(module):
        if name_ == name:
            return _get_fullname(obj)

    if name in get_all_names(module):
        return f"{module}.{name}"

    if "." not in name:
        return None

    name, attr = name.rsplit(".", maxsplit=1)

    for name_, obj in parse(module):
        if name_ == name:
            if isinstance(obj, Module):
                return resolve(f"{obj.name}.{attr}")

            return f"{_get_fullname(obj)}.{attr}"

    return None


# def split_module_name(name: str) -> tuple[str, str | None] | None:
#     for module in iter_attribute_names(name):
#         if not get_module_node(module):
#             continue

#         if module == name:
#             return name, None

#         name_ = name[len(module)+1:]

#         if


def iter_decorator_names(node: ast.AST, module: str) -> Iterator[str]:
    """Yield decorator_names."""
    if not isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
        return

    for deco in node.decorator_list:
        deco_name = next(mkapi.ast.iter_identifiers(deco))

        if name := resolve_from_module(deco_name, module):
            yield name

        else:
            yield deco_name


def has_decorator(node: ast.AST, name: str, module: str) -> bool:
    """Return a decorator expr by name."""
    it = iter_decorator_names(node, module)
    return any(deco_name == name for deco_name in it)


def is_dataclass(node: ast.AST, module: str) -> bool:
    """Return True if the [Class] instance is a dataclass."""
    return has_decorator(node, "dataclasses.dataclass", module)
