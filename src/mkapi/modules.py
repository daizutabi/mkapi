"""Modules."""
from __future__ import annotations

import importlib
import inspect
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType


@dataclass
class Module:
    """Module class."""

    name: str  # Qualified module name.
    obj: ModuleType  # Module object.
    path: Path  # Absolute source file path.
    source: str  # Source text.
    mtime: float  # Modified time.
    members: dict[str, Any]  # Members of the module.

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r})"

    def __getitem__(self, key: str) -> Any:  # noqa: ANN401
        return self.members[key]

    def is_package(self) -> bool:
        """Return True if the module is a package."""
        return self.path.stem == "__init__"

    def update(self) -> None:
        """Update contents."""


def get_members(module: ModuleType) -> dict[str, Any]:
    """Return all members of an object as a (name => value) dictonary."""
    members = {}
    for name, member in inspect.getmembers(module):
        # if not name.startswith("_"):
        #     members[name] = member
        members[name] = member
    return members


def get_module(name: str) -> Module:
    """Return a [Module] instance by name."""
    obj = importlib.import_module(name)
    sourcefile = inspect.getsourcefile(obj)
    if not sourcefile:
        raise NotImplementedError
    path = Path(sourcefile)
    source = inspect.getsource(obj)
    members = get_members(obj)
    mtime = path.stat().st_mtime
    return Module(name, obj, path, source, mtime, members)


def _walk(path: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(path):
        if "__init__.py" not in filenames:
            dirnames.clear()
        else:
            yield Path(dirpath)
            dirnames[:] = [x for x in dirnames if x != "__pycache__"]
        for filename in filenames:
            if not filename.startswith("__") and Path(filename).suffix == ".py":
                yield Path(dirpath) / Path(filename).stem


def _path_to_name(root: Path, name: str) -> Iterator[str]:
    for path in _walk(root):
        yield ".".join((name, *path.relative_to(root).parts))


def get_modulenames(name: str) -> list[str]:
    """Yield submodule names from the package name."""
    module = importlib.import_module(name)
    sourcefile = inspect.getsourcefile(module)
    if not sourcefile:
        return []
    path = Path(sourcefile)
    if path.name != "__init__.py":
        return [name]
    return sorted(_path_to_name(path.parent, name))
