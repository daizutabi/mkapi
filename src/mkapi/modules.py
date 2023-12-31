"""Modules."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING

from mkapi import config

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class Module:
    """Module class."""

    name: str
    path: Path
    source: str
    mtime: float
    node: ast.Module

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r})"

    def is_package(self) -> bool:
        """Return True if the module is a package."""
        return self.path.stem == "__init__"

    def update(self) -> None:
        """Update contents."""

    def __iter__(self) -> Iterator[Module]:
        yield self
        if self.is_package():
            for module in iter_submodules(self):
                yield from module

    def get_tree(self) -> tuple[Module, list]:
        """Return the package tree structure."""
        modules: list[Module | tuple[Module, list]] = []
        for module in find_submodules(self):
            if module.is_package():
                modules.append(module.get_tree())
            else:
                modules.append(module)
        return (self, modules)

    def get_markdown(self, filters: list[str] | None) -> str:
        """Return the markdown text of the module."""
        return "# test\n"


cache: dict[str, Module] = {}


def get_module(name: str) -> Module:
    """Return a [Module] instance by name."""
    spec = find_spec(name)
    if not spec or not spec.origin:
        raise ModuleNotFoundError
    path = Path(spec.origin)
    mtime = path.stat().st_mtime
    if name in cache and mtime == cache[name].mtime:
        return cache[name]
    if not path.exists():
        raise ModuleNotFoundError
    with path.open(encoding="utf-8") as f:
        source = f.read()
    node = ast.parse(source)
    cache[name] = Module(name, path, source, mtime, node)
    return cache[name]


def _is_module(path: Path) -> bool:
    path_str = path.as_posix()
    for pattern in config.exclude:
        if re.search(pattern, path_str):
            return False
    it = (p.name for p in path.iterdir())
    if path.is_dir() and "__init__.py" in it:
        return True
    if path.is_file() and not path.stem.startswith("__") and path.suffix == ".py":
        return True
    return False


def iter_submodules(module: Module) -> Iterator[Module]:
    """Yield submodules."""
    spec = find_spec(module.name)
    if not spec or not spec.submodule_search_locations:
        return
    for location in spec.submodule_search_locations:
        for path in Path(location).iterdir():
            if _is_module(path):
                name = f"{module.name}.{path.stem}"
                yield get_module(name)


def find_submodules(module: Module) -> list[Module]:
    """Return a list of submodules."""
    modules = iter_submodules(module)
    return sorted(modules, key=lambda module: not module.is_package())
