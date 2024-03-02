"""Node module."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.ast import TypeAlias, get_assign_name, is_assign
from mkapi.utils import (
    cache,
    get_export_names,
    get_module_node,
    is_package,
    iter_attribute_names,
    split_name,
)

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Iterator


@dataclass
class Node:
    name: str
    node: AST
    fullname: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.fullname!r})"


@dataclass(repr=False)
class Import(Node):
    node: ast.Import | ast.ImportFrom


@dataclass(repr=False)
class Object(Node):
    fullname: str = field(init=False)
    module: str

    def __post_init__(self):
        self.fullname = f"{self.module}.{self.name}"


@dataclass(repr=False)
class Def(Object):
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Assign(Object):
    node: ast.AnnAssign | ast.Assign | TypeAlias


@dataclass(repr=False)
class Module(Node):
    node: ast.Module
    fullname: str = field(init=False)

    def __post_init__(self):
        self.fullname = self.name


def iter_child_nodes(node: AST, module: str) -> Iterator[Object | Import]:
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.Import):
            for name, fullname in _iter_imports(child):
                yield Import(name, child, fullname)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                yield from _iter_imports_from_star(child, module)

            else:
                it = _iter_imports_from(child, module)
                for name, fullname in it:
                    yield Import(name, child, fullname)

        elif isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            yield Def(child.name, child, module)

        elif is_assign(child) and (name := get_assign_name(child)):
            yield Assign(name, child, module)


def _iter_imports(node: ast.Import) -> Iterator[tuple[str, str]]:
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name

        else:
            for module_name in iter_attribute_names(alias.name):
                yield module_name, module_name


def _get_module(node: ast.ImportFrom, module: str) -> str:
    if not node.level and node.module:
        return node.module

    names = module.split(".")

    if is_package(module):
        prefix = ".".join(names[: len(names) - node.level + 1])

    else:
        prefix = ".".join(names[: -node.level])

    return f"{prefix}.{node.module}" if node.module else prefix


def _iter_imports_from(node: ast.ImportFrom, module: str) -> Iterator[tuple[str, str]]:
    module = _get_module(node, module)

    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _iter_imports_from_star(node: ast.ImportFrom, module: str) -> Iterator[Object | Import]:
    module = _get_module(node, module)

    if not (node_ := get_module_node(module)):
        return

    names = get_export_names(module)

    for child in iter_child_nodes(node_, module):
        if child.name.startswith("_"):
            continue

        if not names or child.name in names:
            yield child


@cache
def get_child_nodes(node: AST, module: str) -> list[Object | Import]:
    node_dict: dict[str, list[Object | Import]] = {}

    for child in iter_child_nodes(node, module):
        if child.name not in node_dict:
            node_dict[child.name] = [child]

        else:
            nodes = node_dict[child.name]
            if not isinstance(nodes[-1], Def) or not isinstance(child, Def):
                nodes.clear()

            nodes.append(child)

    return list(chain(*node_dict.values()))


def iter_nodes(fullname: str) -> Iterator[Module | Object | Import]:
    if node := get_module_node(fullname):
        yield Module(fullname, node)
        return

    if "." not in fullname:
        return

    module, name = fullname.rsplit(".", maxsplit=1)

    if not (node := get_module_node(module)):
        return

    for member in get_child_nodes(node, module):
        if member.name == name:
            if not isinstance(member, Import):
                yield member

            elif member.fullname != fullname:
                yield from iter_nodes(member.fullname)


@cache
def parse(node: AST, module: str) -> list[tuple[str, Module | Object | Import]]:
    members = []

    for member in get_child_nodes(node, module):
        name = member.name

        if isinstance(member, Import) and (resolved := list(iter_nodes(member.fullname))):
            members.extend((name, r) for r in resolved)

        else:
            members.append((name, member))

    return members


@cache
def resolve(name: str, module: str | None = None) -> tuple[str | None, str | None] | None:
    if not module:
        if not (name_module := split_name(name)):
            return None

        name, module = name_module
        if not module:
            return name, None

    if not (node := get_module_node(module)):
        return None

    names = name.split(".")
    for name_, obj in parse(node, module):
        if name_ == names[0]:
            qualname = ".".join([obj.name, *names[1:]])
            if isinstance(obj, Module):
                return resolve(qualname)

            if isinstance(obj, Object):
                return qualname, obj.module

            if isinstance(obj, Import):
                return None, obj.fullname

    return name, module


@cache
def resolve_from_module(name: str, module: str | None) -> str | None:
    if not (name_module := resolve(name, module)):
        return None

    name_, module = name_module

    if not module:
        return name_

    if not name_:
        return module

    return f"{module}.{name_}"
