"""Import module."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING

import mkapi.ast
from mkapi.utils import (
    get_by_name,
    get_module_node,
    get_module_path,
    iter_identifiers,
    iter_parent_module_names,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(repr=False)
class Name:
    """Import class for [Module]."""

    name: str
    fullname: str

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


@dataclass(repr=False)
class Import(Name):
    """Import class for [Module]."""


@dataclass(repr=False)
class Global(Name):
    """Import class for [Module]."""


def _iter_objects(module: str) -> Iterator[str]:
    if not (node := get_module_node(module)):
        return
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            yield f"{module}.{child.name}"
        elif isinstance(child, ast.AnnAssign | ast.Assign | ast.TypeAlias):  # noqa: SIM102
            if assign_name := mkapi.ast.get_assign_name(child):  # noqa: SIM102
                # if isinstance(child, ast.Assign) and assign_name == "__all__":
                #     for name in _iter_objects_from_all(child):
                #         yield f"{module}.{name}"
                if not assign_name.startswith("__"):
                    yield f"{module}.{assign_name}"


def _iter_objects_from_all(node: ast.Assign) -> Iterator[str]:
    if not isinstance(node.value, ast.List):
        return
    for c in node.value.elts:
        if isinstance(c, ast.Constant) and isinstance(c.value, str):
            yield c.value


def _iter_imports(module: str) -> Iterator[Import]:
    if not (node := get_module_node(module)):
        return
    for child in mkapi.ast.iter_child_nodes(node):
        if isinstance(child, ast.Import):
            for name, fullname in _iter_imports_from_import(child):
                yield Import(f"{module}.{name}", fullname)
        elif isinstance(child, ast.ImportFrom):
            for name, fullname in _iter_imports_from_import_from(child, module):
                yield Import(f"{module}.{name}", fullname)


def _iter_imports_from_import(node: ast.Import) -> Iterator[tuple[str, str]]:
    for alias in node.names:
        if alias.asname:
            yield alias.asname, alias.name
        else:
            for module_name in iter_parent_module_names(alias.name):
                yield module_name, module_name


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


@cache
def resolve(name: str) -> str | None:
    """Resolve name."""
    if get_module_path(name) or "." not in name:
        return name
    module, _ = name.rsplit(".", maxsplit=1)
    if name in _iter_objects(module):
        return name
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


@dataclass(repr=False)
class Globals:
    """Globals class."""

    names: list[Import | Global]


def _iter_globals(module: str) -> Iterator[Global | Import]:
    n = len(module) + 1
    for name in _iter_objects(module):
        yield Global(name[n:], name)
    for import_ in _iter_imports(module):
        name = import_.name[n:]
        if fullname := resolve(import_.fullname):
            yield Import(name, fullname)
        else:
            yield Import(name, import_.fullname)


@cache
def get_globals(module: str) -> Globals:
    """Return a global list of a module."""
    return Globals(list(_iter_globals(module)))


@cache
def get_fullname(module: str, name: str) -> str | None:
    """Return the fullname of an object in the module."""
    if name.startswith(module) or module.startswith(name):
        return name
    names = get_globals(module).names
    if global_ := get_by_name(names, name):
        return global_.fullname
    if "." not in name:
        return None
    name_, attr = name.rsplit(".", maxsplit=1)
    global_ = get_by_name(names, name_)
    if isinstance(global_, Global):
        return f"{global_.fullname}.{attr}"
    if isinstance(global_, Import):
        return resolve(f"{global_.fullname}.{attr}")
    return name
    # return None


def _get_link(module: str, name: str, asname: str) -> str:
    fullname = get_fullname(module, name)
    asname = asname.replace("_", "\\_")
    return f"[{asname}][__mkapi__.{fullname}]" if fullname else asname


@cache
def get_link_from_type(module: str, name: str, *, is_object: bool = False) -> str:
    """Return markdown links from type."""
    names = []
    parents = iter_parent_module_names(name)
    asnames = name.split(".")
    for name, asname in zip(parents, asnames, strict=True):
        names.append(_get_link(module, name, asname))
    return "..".join(names) if is_object else ".".join(names)


def get_link_from_type_string(module: str, source: str) -> str:
    """Return markdown links from string-type."""
    strs = []
    for name, isidentifier in iter_identifiers(source):
        if isidentifier:
            strs.append(get_link_from_type(module, name, is_object=False))
        else:
            strs.append(name)
    return "".join(strs)


# LINK_PATTERN = re.compile(r"(?<!\])\[([^[\]\s\(\)]+?)\](\[\])?(?![\[\(])")


# def get_link_from_text(module: str, text: str, *, name_only: bool = False) -> str:
#     """Return markdown links from text."""

#     def replace(match: re.Match) -> str:
#         name = match.group(1)
#         link = get_link_from_type(module, name, is_object=False)
#         if name != link:
#             return link
#         return name if name_only else match.group()

#     return re.sub(LINK_PATTERN, replace, text)