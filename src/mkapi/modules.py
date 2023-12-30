"""Modules."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING

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


def get_module(name: str) -> Module:
    """Return a [Module] instance by name."""
    spec = find_spec(name)
    if not spec or not spec.origin:
        raise ModuleNotFoundError
    path = Path(spec.origin)
    if not path.exists():
        raise ModuleNotFoundError
    with path.open(encoding="utf-8") as f:
        source = f.read()
    node = ast.parse(source)
    mtime = path.stat().st_mtime
    return Module(name, path, source, mtime, node)


def iter_submodules(module: Module) -> Iterator[Module]:
    """Yield submodules."""
    spec = find_spec(module.name)
    if not spec or not spec.submodule_search_locations:
        return
    for location in spec.submodule_search_locations:
        for path in Path(location).iterdir():
            if path.suffix == ".py":
                name = f"{module.name}.{path.stem}"
                yield get_module(name)


def find_submodules(module: Module) -> list[Module]:
    """Return a list of submodules."""
    return list(iter_submodules(module))
