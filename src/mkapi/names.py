"""Node module."""
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
    get_module_path,
    is_package,
    iter_parent_module_names,
)

try:
    from ast import TypeAlias
except ImportError:
    TypeAlias = None

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(repr=False)
class Name:
    """Name class."""

    module: str
    name: str
    fullname: str
    node: ast.AST

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.module,self.name,self.fullname})"


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


def _iter_names(module: str) -> Iterator[Object | Assign | Import]:
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
            for name, fullname in _iter_imports_from_import_from(child, module):
                yield Import(module, name, fullname, child)


def _iter_imports_from_import(node: ast.Import) -> Iterator[tuple[str, str]]:
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name

        else:
            for module_name in iter_parent_module_names(alias.name):
                yield module_name, module_name


def _iter_imports_from_import_from(node: ast.ImportFrom, parent: str) -> Iterator[tuple[str, str]]:
    if not node.module:
        module = parent

    elif node.level:
        names = parent.split(".")

        if is_package(parent):  # noqa: SIM108
            prefix = ".".join(names[: len(names) - node.level + 1])

        else:
            prefix = ".".join(names[: -node.level])

        module = f"{prefix}.{node.module}"

    else:
        module = node.module

    for alias in node.names:
        yield alias.asname or alias.name, f"{module}.{alias.name}"


def _resolve(import_: Import) -> Module | Object | Assign | None:
    fullname = import_.fullname

    if node := get_module_node(fullname):
        return Module(fullname, node)

    if "." not in fullname:
        return Module(fullname, None)

    module, name = fullname.rsplit(".", maxsplit=1)

    if member := get_by_name(_iter_names(module), name):
        if isinstance(member, Object | Assign):
            return member

        return _resolve(member)

    return None


def get_members(module: str) -> dict[str, Module | Object | Assign]:
    members = {}

    for member in _iter_names(module):
        if isinstance(member, Object | Assign):
            members[member.name] = member

        elif resolved := _resolve(member):
            members[member.name] = resolved

    return members


@cache
def resolve(name: str) -> str | None:
    """Resolve name."""
    if get_module_path(name) or "." not in name:
        return name

    module, _ = name.rsplit(".", maxsplit=1)

    if obj := get_by_name(_iter_objects(module), name):
        return obj.fullname

    if assign := get_by_name(_iter_assigns(module), name):
        return assign.fullname

    if import_ := get_by_name(_iter_imports(module), name):
        if name == import_.fullname:
            return None

        return resolve(import_.fullname)

    return None


def resolve_with_attribute(name: str) -> str | None:
    """Resolve name with attribute."""
    if fullname := resolve(name):
        return fullname

    if "." in name:
        name_, attr = name.rsplit(".", maxsplit=1)
        if fullname := resolve(name_):
            return f"{fullname}.{attr}"

    return None


def _iter_globals(module: str) -> Iterator[Object | Import]:
    n = len(module) + 1
    for name in _iter_objects(module):
        yield Object(name[n:], name)
    for import_ in _iter_imports(module):
        name = import_.name[n:]
        if fullname := resolve(import_.fullname):
            yield Import(name, fullname)
        else:
            yield Import(name, import_.fullname)


@cache
def get_globals(module: str) -> list[Object | Import]:
    """Return a global list of a module."""
    return list(_iter_globals(module))


@cache
def get_fullname(name: str, module: str) -> str | None:
    """Return the fullname of an object in the module."""
    if name.startswith(module) or module.startswith(name):
        return name
    names = get_globals(module)
    if global_ := get_by_name(names, name):
        return global_.fullname
    if "." not in name:
        return None
    name_, attr = name.rsplit(".", maxsplit=1)
    global_ = get_by_name(names, name_)
    if isinstance(global_, Object):
        return f"{global_.fullname}.{attr}"
    if isinstance(global_, Import):
        return resolve(f"{global_.fullname}.{attr}")
    return name


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
