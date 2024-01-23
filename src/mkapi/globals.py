"""Import module."""

from __future__ import annotations

import ast
from functools import cache
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.utils import get_module_node, get_module_path, iter_parent_module_names

if TYPE_CHECKING:
    from collections.abc import Iterator


@cache
def _get_objects(name: str) -> list[str]:
    return list(_iter_objects(name))


@cache
def _get_imports(name: str) -> list[tuple[str, str]]:
    return list(_iter_imports(name))


def _iter_objects(name: str) -> Iterator[str]:
    yield name
    if not (node := get_module_node(name)):
        return
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            yield f"{name}.{child.name}"
        elif isinstance(child, ast.AnnAssign | ast.Assign | ast.TypeAlias):  # noqa: SIM102
            if assign_name := mkapi.ast.get_assign_name(child):  # noqa: SIM102
                if not assign_name.startswith("__"):
                    yield f"{name}.{assign_name}"


def _iter_imports(name: str) -> Iterator[tuple[str, str]]:
    if not (node := get_module_node(name)):
        return
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.Import):
            for name_, fullname in _iter_imports_from_import(child):
                yield f"{name}.{name_}", fullname
        elif isinstance(child, ast.ImportFrom):
            for name_, fullname in _iter_imports_from_import_from(child, name):
                yield f"{name}.{name_}", fullname


def _iter_imports_from_import(node: ast.Import) -> Iterator[tuple[str, str]]:
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name
        else:
            for name in iter_parent_module_names(alias.name):
                yield name, name


def _iter_imports_from_import_from(
    node: ast.ImportFrom,
    parent: str,
) -> Iterator[tuple[str, str]]:
    if not node.module:
        module = parent
    elif node.level:
        names = parent.split(".")
        prefix = ".".join(names[: len(names) - node.level + 1])
        module = f"{prefix}.{node.module}"
    else:
        module = node.module
    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _resolve(name: str) -> str | None:
    if get_module_path(name) or "." not in name:
        return name
    module, _ = name.rsplit(".", maxsplit=1)
    if name in _get_objects(module):
        return name
    for name_, fullname in _get_imports(module):
        if name_ == name:
            return _resolve(fullname)
    return None


@cache
def get_globals(name: str) -> list[tuple[str, str]]:
    """Return a global dictionary of a module."""
    return list(_iter_globals(name))


def _iter_globals(name: str) -> Iterator[tuple[str, str]]:
    n = len(name) + 1
    for name_ in _iter_objects(name):
        if name_ != name:
            yield name_[n:], name_[n:]
    for name_, fullname in _iter_imports(name):
        yield name_[n:], _resolve(fullname) or fullname


# def get_member(module: Module, name: str) -> Class | Function | Attribute | None:
#     """Return a member instance by the name."""
#     if obj := get_by_name(module.classes, name):
#         return obj
#     if obj := get_by_name(module.functions, name):
#         return obj
#     if obj := get_by_name(module.attributes, name):
#         return obj
#     return None


# def get_fullname_from_import(import_: Import) -> str | None:
#     fullname = import_.fullname
#     if module := load_module(fullname):
#         return fullname
#     if "." in fullname:
#         name, attr = fullname.rsplit(".", maxsplit=1)
#         if module := load_module(name):
#             return get_fullname(module, attr)
#     return None


# def get_fullname(module: Module, name: str) -> str | None:
#     """Return the fullname of an object in the module."""
#     if obj := get_member(module, name):
#         return obj.fullname
#     if import_ := get_by_name(module.imports, name):
#         return import_.fullname  # TODO: resolve without 'load_module'
#     if "." in name:
#         name_, attr = name.rsplit(".", maxsplit=1)
#         if import_ := get_by_name(module.imports, name_):  # noqa: SIM102
#             if module_ := load_module(import_.fullname):  # noqa: SIM102
#                 if fullname := get_fullname(module_, attr):
#                     return fullname
#     if name.startswith(module.name):
#         return name
#     return None


# @dataclass(repr=False)
# class Import:
#     """Import class for [Module]."""

#     name: str
#     fullname: str | None
#     # from_: str | None
#     # level: int

#     def __repr__(self) -> str:
#         return f"{self.__class__.__name__}({self.name!r})"


# def _iter_imports_from_import(
#     node: ast.Import | ast.ImportFrom,
# ) -> Iterator[tuple[str, str, int]]:
#     for alias in node.names:
#         if isinstance(node, ast.Import):
#             if alias.asname:
#                 yield alias.asname, alias.name, 0
#             else:
#                 for fullname in iter_parent_module_names(alias.name):
#                     yield fullname, fullname, 0
#         else:
#             name = alias.asname or alias.name
#             fullname = f"{node.module}.{alias.name}"
#             yield name, fullname, node.level


# def _iter_imports_from_module(node: ast.Module) -> Iterator[tuple[str, str, int]]:
#     for child in mkapi.ast.iter_child_nodes(node):
#         if isinstance(child, ast.Import | ast.ImportFrom):
#             yield from _iter_imports_from_import(child)


# def _iter_imports_relative(node: ast.Module, name: str) -> Iterator[tuple[str, str]]:
#     """Yield [Import] instances."""
#     names = name.split(".")
#     n = len(names)
#     for name_, fullname, level in _iter_imports_from_module(node):
#         if level:
#             prefix = ".".join(names[: n - level + 1])
#             yield name_, f"{prefix}.{fullname}"
#         else:
#             yield name_, fullname


# def _get_fullname(fullname: str) -> str | None:
#     if get_module_path(fullname):
#         return fullname
#     if "." not in fullname:
#         return None
#     module, name = fullname.rsplit(".", maxsplit=1)
#     if not (node := get_module_node(module)):
#         return None
#     print("AA", module)
#     for name_, fullname_ in _iter_imports_relative(node, module):
#         print("BB", name_, fullname_)
#         if name_ == name:
#             return _get_fullname(fullname_)
#     return fullname


# def iter_imports(node: ast.Module, name: str) -> Iterator[Import]:
#     """Yield [Import] instances."""
#     for name_, fullname in _iter_imports_relative(node, name):
#         # yield Import(name_, _get_fullname(fullname))
#         yield Import(name_, fullname)
