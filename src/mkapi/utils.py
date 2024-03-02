"""Utility code."""

from __future__ import annotations

import ast
import dataclasses
import functools
import importlib
import inspect
import re
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator


cached_objects = []

T = TypeVar("T")


@overload
def cache(obj: Callable[..., T]) -> Callable[..., T]: ...  # no cov


@overload
def cache(obj: dict) -> dict: ...  # no cov


@overload
def cache(obj: list) -> list: ...  # no cov


def cache(obj: Callable[..., T] | dict | list) -> Callable[..., T] | dict | list:
    """Cache a function and register it to clear cache."""
    if callable(obj):
        cached = functools.cache(obj)
        cached_objects.append(cached)
        return cached
    cached_objects.append(obj)
    return obj


def cache_clear() -> None:
    """Clear cache."""
    for obj in cached_objects:
        if callable(obj):
            obj.cache_clear()
        else:
            obj.clear()


@cache
def get_module_path(name: str) -> Path | None:
    """Return the source path of the module name."""
    try:
        spec = find_spec(name)
    except (ModuleNotFoundError, ValueError):
        return None
    if not (spec and spec.origin):
        return None
    path = Path(spec.origin)
    if not path.exists() or path.suffix != ".py":  # for builtin, frozen
        return None
    return path


@cache
def get_module_name(module: str) -> str:
    if not module:
        return ""

    try:
        return importlib.import_module(module).__name__
    except ModuleNotFoundError:
        return module


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


def is_package(name: str) -> bool:
    """Return True if the name is a package."""
    try:
        spec = find_spec(name)
    except ModuleNotFoundError:
        return False
    if spec and spec.origin:
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


def find_submodule_names(
    name: str,
    predicate: Callable[[str], bool] | None = None,
) -> list[str]:
    """Return a list of submodule names.

    Optionally, only return submodules that satisfy a given predicate.
    """
    predicate = predicate or (lambda _: True)
    names = [name for name in iter_submodule_names(name) if predicate(name)]
    names.sort(key=lambda x: [not is_package(x), x.replace("_", "~")])
    return names


module_cache: dict[str, float] = {}


def is_module_cache_dirty(name: str) -> bool:
    """Return True if `module_cache` is dirty."""
    if not (path := get_module_path(name)):
        return False
    if not (mtime := module_cache.get(name)):
        return True
    return mtime != path.stat().st_mtime


@cache
def get_module_node_source(name: str) -> tuple[ast.Module, str] | None:
    """Return a tuple of ([ast.Module], source) from a module name."""

    if path := get_module_path(name):
        with path.open("r", encoding="utf-8") as f:
            source = f.read()

    else:
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError:
            return None

        try:
            source = inspect.getsource(module)
        except (OSError, TypeError):
            return None

    node = ast.parse(source)
    mtime = path.stat().st_mtime if path else 0
    module_cache[name] = mtime

    return node, source


def get_module_node(name: str) -> ast.Module | None:
    """Return an [ast.Module] instance from a module name."""
    if node_source := get_module_node_source(name):
        return node_source[0]

    return None


def get_module_source(name: str) -> str | None:
    """Return an [ast.Module] instance from a module name."""
    if node_source := get_module_node_source(name):
        return node_source[1]

    return None


def iter_attribute_names(fullname: str, *, reverse: bool = False) -> Iterator[str]:
    """Yield parent module names.

    Examples:
        >>> list(iter_parent_module_names("a.b.c.d"))
        ['a', 'a.b', 'a.b.c', 'a.b.c.d']
        >>> list(iter_parent_module_names("a.b.c.d", reverse=True))
        ['a.b.c.d', 'a.b.c', 'a.b', 'a']
    """
    names = fullname.split(".")
    it = range(len(names), 0, -1) if reverse else range(1, len(names) + 1)
    for k in it:
        yield ".".join(names[:k])


T = TypeVar("T")


def _is_equal(item, name: str, attr: str = "name") -> bool:
    return getattr(item, attr) == name


def iter_by_name(items: Iterable[T], name: str, attr: str = "name") -> Iterator[T]:
    """Yield items with a name from an item list."""
    for item in items:
        if _is_equal(item, name, attr):
            yield item


def get_by_name(items: Iterable[T], name: str | Iterable[str], attr: str = "name") -> T | None:
    """Get the first item with a name from an item list."""
    if not isinstance(name, str):
        for name_ in name:
            if item := get_by_name(items, name_):
                return item

        return None

    for item in iter_by_name(items, name, attr):
        return item
    return None


def get_by_kind(items: Iterable[T], kind: str) -> T | None:
    """Get the first item with a kind from an item list."""
    for item in iter_by_name(items, kind, attr="kind"):
        return item
    return None


def get_by_type(items: Iterable, type_: type[T]) -> T | None:
    """Get the first item with a type from an item list."""
    for item in items:
        if isinstance(item, type_):
            return item
    return None


def del_by_name(items: list[T], name: str, attr: str = "name") -> None:
    """Delete the first item with a name from an item list.

    The first argument `items` is changed in-place.
    """
    for k, item in enumerate(items):
        if _is_equal(item, name, attr):
            del items[k]
            return


def unique_names(a: Iterable, b: Iterable, attr: str = "name") -> list[str]:
    """Return unique names from two iterables."""
    names = [getattr(x, attr) for x in a]
    for x in b:
        if (name := getattr(x, attr)) not in names:
            names.append(name)
    return names


def split_filters(name: str) -> tuple[str, list[str]]:
    """Split filters written after `|`.

    Examples:
        >>> split_filters("a.b.c")
        ('a.b.c', [])
        >>> split_filters("a.b.c|upper|strict")
        ('a.b.c', ['upper', 'strict'])
        >>> split_filters("|upper|strict")
        ('', ['upper', 'strict'])
        >>> split_filters("")
        ('', [])
    """
    index = name.find("|")
    if index == -1:
        return name, []
    name, filters = name[:index], name[index + 1 :]
    return name, filters.split("|")


def update_filters(org: list[str], update: list[str]) -> list[str]:
    """Update filters.

    Examples:
        >>> update_filters(["upper"], ["lower"])
        ['lower']
        >>> update_filters(["lower"], ["upper"])
        ['upper']
        >>> update_filters(["long"], ["short"])
        ['short']
        >>> update_filters(["short"], ["long"])
        ['long']
    """
    filters = org + update
    for x, y in [["lower", "upper"], ["long", "short"]]:
        if x in org and y in update:
            del filters[filters.index(x)]
        if y in org and x in update:
            del filters[filters.index(y)]
    return filters


def is_identifier(name: str) -> bool:
    """Return True if name is identifier with dot."""
    return name != "" and all(x.isidentifier() for x in name.split("."))


def iter_identifiers(source: str) -> Iterator[tuple[str, bool]]:
    """Yield identifiers as a tuple of (name, isidentifier)."""
    start = stop = 0
    while start < len(source):
        c = source[start]
        if c.isidentifier():
            stop = start + 1
            while stop < len(source):
                c = source[stop]
                if c == "." or c.isdigit() or c.isidentifier():
                    stop += 1
                else:
                    break
            if source[stop - 1] == ".":
                yield source[start : stop - 1], True
                yield ".", False
            else:
                yield source[start:stop], True
            start = stop
        elif c in ['"', "'"]:
            stop = start + 1
            while stop < len(source):
                if source[stop] != source[start]:
                    stop += 1
                else:
                    break
            yield source[start : stop + 1], False
            start = stop + 1
        else:
            yield c, False
            start += 1


@cache
def get_export_names(module: str) -> list[str]:
    try:
        members = importlib.import_module(module).__dict__
    except ModuleNotFoundError:
        return []

    names = members.get("__all__")
    if isinstance(names, list | tuple):
        return list(names)

    return []


@cache
def get_object_from_module(name: str, module: str) -> object | None:
    try:
        obj = importlib.import_module(module or name)
    except ModuleNotFoundError:
        return None

    for name_ in name.split("."):
        if not (obj := dict(inspect.getmembers(obj)).get(name_)):
            return None

    return obj


@cache
def is_dataclass(name: str, module: str) -> bool:
    obj = get_object_from_module(name, module)
    return dataclasses.is_dataclass(obj)


@cache
def get_base_classes(name: str, module: str) -> list[tuple[str, str]]:
    obj = get_object_from_module(name, module)

    bases = []

    if inspect.isclass(obj):
        for base in obj.__bases__:
            if base.__module__ != "builtins":
                basename = next(iter_identifiers(base.__name__))[0]
                bases.append((basename, base.__module__))

    return bases


@cache
def split_name(name: str) -> tuple[str, str | None] | None:
    modulename = None
    for module in iter_attribute_names(name):
        if not get_module_node(module):
            if not modulename:
                return None

            return name[len(modulename) + 1 :], modulename

        modulename = module

    return name, None
