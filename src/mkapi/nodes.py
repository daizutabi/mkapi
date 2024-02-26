"""Node module."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.utils import get_module_node, is_package, iter_attribute_names

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
            for name, fullname in _iter_imports(child):
                yield Import(name, child, module, fullname)

        elif isinstance(child, ast.ImportFrom):
            if child.names[0].name == "*":
                yield from _iter_imports_from_star(child, module)

            else:
                it = _iter_imports_from(child, module)
                for name, fullname in it:
                    yield Import(name, child, module, fullname)

        elif isinstance(child, ast.AnnAssign | ast.Assign | TypeAlias):
            if name := mkapi.ast.get_assign_name(child):
                yield Object(name, child, module)

        elif isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            yield Object(child.name, child, module)


def _iter_imports(node: ast.Import) -> Iterator[tuple[str, str]]:
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name

        else:
            for module_name in iter_attribute_names(alias.name):
                yield module_name, module_name


def _get_module(node: ast.ImportFrom, module: str) -> str:
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


def _iter_imports_from(
    node: ast.ImportFrom,
    module: str,
) -> Iterator[tuple[str, str]]:
    module = _get_module(node, module)
    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _iter_imports_from_star(
    node: ast.ImportFrom,
    module: str,
) -> Iterator[Object | Import]:
    module = _get_module(node, module)
    if node_ := get_module_node(module):
        yield from _iter_nodes(node_, module)


def resolve(fullname: str) -> Iterator[Module | Object | Import]:
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

            yield from resolve(member.fullname)


def parse(node: ast.Module, module: str) -> list[tuple[str, Module | Object | Import]]:
    members = []

    for member in _iter_nodes(node, module):
        name = member.name

        if isinstance(member, Import):
            if resolved := list(resolve(member.fullname)):
                members.extend((name, x) for x in resolved)
            else:
                members.append((name, member))

        else:
            members.append((name, member))

    return members
