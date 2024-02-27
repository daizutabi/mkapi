"""Node module."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.ast import TypeAlias, get_assign_name, is_assign
from mkapi.utils import cache, get_export_names, get_module_node, is_package, iter_attribute_names

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class Node:
    name: str
    node: ast.AST


@dataclass
class Import(Node):
    node: ast.Import | ast.ImportFrom
    fullname: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.fullname!r})"


@dataclass
class Object(Node):
    module: str

    def __repr__(self) -> str:
        fullname = f"{self.module}.{self.name}"
        return f"{self.__class__.__name__}({fullname!r})"


@dataclass(repr=False)
class Def(Object):
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(repr=False)
class Assign(Object):
    node: ast.AnnAssign | ast.Assign | TypeAlias


@dataclass
class Module(Node):
    node: ast.Module

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


def iter_child_nodes(node: ast.AST, module: str) -> Iterator[Object | Import]:
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

    if node_ := get_module_node(module):
        names = get_export_names(module)
        for child in iter_child_nodes(node_, module):
            if child.name.startswith("_"):
                continue

            if not names or child.name in names:
                yield child


@cache
def get_child_nodes(node: ast.Module, name: str) -> list[Object | Import]:
    node_dict: dict[str, list[Object | Import]] = {}

    for child in iter_child_nodes(node, name):
        if child.name not in node_dict:
            node_dict[child.name] = [child]

        else:
            nodes = node_dict[child.name]
            if not isinstance(nodes[-1], Def) or not isinstance(child, Def):
                nodes.clear()

            nodes.append(child)

    return list(chain(*node_dict.values()))


def resolve(fullname: str) -> Iterator[Module | Object | Import]:
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
                yield from resolve(member.fullname)


@cache
def parse(node: ast.Module, module: str) -> list[tuple[str, Module | Object | Import]]:
    members = []

    for member in get_child_nodes(node, module):
        name = member.name

        if isinstance(member, Import) and (resolved := list(resolve(member.fullname))):
            members.extend((name, r) for r in resolved)

        else:
            members.append((name, member))

    return members
