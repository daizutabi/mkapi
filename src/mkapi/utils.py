"""Utility code."""
from __future__ import annotations

import re
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


def _is_module(path: Path, exclude_patterns: Iterable[str] = ()) -> bool:
    path_str = path.as_posix()
    for pattern in exclude_patterns:
        if re.search(pattern, path_str):
            return False
    it = (p.name for p in path.iterdir())
    if path.is_dir() and "__init__.py" in it:
        return True
    if path.is_file() and not path.stem.startswith("__") and path.suffix == ".py":
        return True
    return False


def _is_package(name: str) -> bool:
    if (spec := find_spec(name)) and spec.origin:
        return Path(spec.origin).stem == "__init__"
    return False


def iter_submodule_names(name: str) -> Iterator[str]:
    """Yield submodule names."""
    spec = find_spec(name)
    if not spec or not spec.submodule_search_locations:
        return
    for location in spec.submodule_search_locations:
        for path in Path(location).iterdir():
            if _is_module(path):
                yield f"{name}.{path.stem}"


def find_submodule_names(name: str) -> list[str]:
    """Return a list of submodules."""
    names = iter_submodule_names(name)
    return sorted(names, key=lambda name: not _is_package(name))
