"""
Utility Functions Module

This module contains a collection of utility functions that provide various
helper functionalities for the application. These functions are designed to
be reusable and facilitate common tasks such as module introspection,
caching, and object retrieval.

The functions in this module are organized to enhance code readability and
maintainability, allowing developers to easily access and utilize common
operations without the need to rewrite code.

Key Features:
- Caching: Functions to cache results of expensive operations and clear
  the cache when necessary.
- Module Management: Functions to retrieve module paths, names, and
  check if a module is a package or a valid module.
- Object Retrieval: Functions to dynamically retrieve objects from
  specified modules, including support for nested objects.
- Identifier Validation: Functions to validate and iterate over
  identifiers in source code.
- Submodule Discovery: Functions to find and iterate over submodules
  within a package.

This module is intended for internal use within the application and may
be subject to changes as the application evolves. Developers are encouraged
to refer to the function docstrings for detailed information on each
function's purpose, parameters, and return values.
"""

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
    """Cache a function or data structure and register it for cache clearing.

    This function accepts a callable (function) or a data structure (dictionary or list)
    and caches it. If a callable is provided, it wraps it with a caching mechanism
    and stores it in a global list of cached objects. If a dictionary or list is provided,
    it is simply added to the cache list.

    Args:
        obj (Callable[..., T] | dict | list): The object to cache, which can be a
            callable function, a dictionary, or a list.

    Returns:
        Callable[..., T] | dict | list: The cached object, which is either the cached
        function or the original dictionary/list.

    Examples:
        >>> @cache
        ... def my_function(x):
        ...     return x * 2
        >>> cached_function = cache(my_function)
        >>> cached_function(5)
        10

        >>> my_dict = {'key': 'value'}
        >>> cached_dict = cache(my_dict)
        >>> cached_dict['key']
        'value'

    This function is useful for optimizing performance by caching results of expensive
    function calls or storing frequently used data structures for quick access.
    """
    if callable(obj):
        cached = functools.cache(obj)
        cached_objects.append(cached)
        return cached
    cached_objects.append(obj)
    return obj


def cache_clear() -> None:
    """Clear the cache of all cached objects.

    This function iterates through the global list of cached objects and clears
    the cache for each object. If the object is callable (a function), it calls
    the `cache_clear` method on that function to clear its cache. If the object
    is a dictionary or list, it clears the contents of that object.

    Returns:
        None: This function does not return any value.

    This function is useful for managing memory and ensuring that cached data
    is up-to-date, especially in scenarios where the underlying data may change.
    """
    for obj in cached_objects:
        if callable(obj):
            obj.cache_clear()
        else:
            obj.clear()


@cache
def get_module_path(name: str) -> Path | None:
    """Return the source path of the specified module name.

    This function attempts to find the source path of a module given its name.
    It uses the `find_spec` function to retrieve the module specification and
    checks if the module has a valid origin. If the module is found and is a
    Python file, the function returns its path. If the module cannot be found
    or is not a valid Python file, it returns None.

    Args:
        name (str): The name of the module whose source path is to be retrieved.

    Returns:
        Path | None: The source path of the module as a Path object, or None
        if the module does not exist or is not a valid Python file.

    Examples:
        >>> path = get_module_path("collections")
        >>> path.exists()
        True

        >>> path = get_module_path("non_existent_module")
        >>> path is None
        True

    This function is useful for dynamically locating the source files of modules,
    which can be helpful for introspection, documentation generation, or analysis.
    """
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
    """Return the name of the specified module.

    This function attempts to import a module given its name and returns
    the module's name as a string. If the module name is empty, it returns
    an empty string. If the module cannot be found, it returns the original
    module name provided.

    Args:
        module (str): The name of the module to import.

    Returns:
        str: The name of the imported module, or the original module name
        if the import fails or if the input is empty.

    Examples:
        >>> get_module_name("os")
        'os'

        >>> get_module_name("non_existent_module")
        'non_existent_module'

        >>> get_module_name("")
        ''

    This function is useful for dynamically retrieving the name of a module,
    especially in scenarios where the module name may be provided as a string
    and needs to be validated or processed.
    """
    if not module:
        return ""

    try:
        return importlib.import_module(module).__name__
    except ModuleNotFoundError:
        return module


def _is_module(path: Path, exclude_patterns: Iterable[str] = ()) -> bool:
    """Determine if the given path is a module.

    This function checks whether the specified path represents a Python module.
    It considers both directories and files. A directory is considered a module
    if it contains an `__init__.py` file. A file is considered a module if it
    has a `.py` extension and does not start with a double underscore.

    Args:
        path (Path): The path to check.
        exclude_patterns (Iterable[str], optional): A list of regex patterns to
            exclude certain paths from being considered as modules.
            Defaults to an empty iterable.

    Returns:
        bool: True if the path is a module; otherwise, False.

    This function is useful for identifying Python modules in a directory structure,
    which can be helpful for module discovery and introspection.
    """
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
    """Return True if the specified name is a package.

    This function checks if the given name corresponds to a Python package.
    A package is identified by the presence of an `__init__.py` file in its
    directory. The function attempts to find the module specification using
    `find_spec` and checks if the module's origin is the `__init__.py` file.

    Args:
        name (str): The name of the module to check.

    Returns:
        bool: True if the name is a package; otherwise, False.

    This function is useful for determining whether a given module name
    corresponds to a package, which can be important for module discovery
    and organization in Python projects.
    """
    try:
        spec = find_spec(name)
    except ModuleNotFoundError:
        return False

    if spec and spec.origin:
        return Path(spec.origin).stem == "__init__"

    return False


def iter_submodule_names(name: str) -> Iterator[str]:
    """Yield the names of submodules for the specified module.

    This function retrieves the submodule names associated with a given
    module name. It uses the `find_spec` function to obtain the module
    specification and checks for submodule search locations. For each
    valid submodule path, it yields the full name of the submodule.

    Args:
        name (str): The name of the module for which to yield submodule names.

    Yields:
        str: The full names of the submodules found under the specified module.

    This function is useful for dynamically discovering submodules within
    a package, which can be helpful for module introspection and organization.
    """
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

    This function retrieves the names of submodules associated with a given
    module name. It optionally filters the submodule names based on a
    provided predicate function. If no predicate is provided, all submodule
    names are returned.

    Args:
        name (str): The name of the module for which to find submodule names.
        predicate (Callable[[str], bool] | None): An optional function that takes
            a submodule name as input and returns True if the submodule should
            be included in the result. Defaults to None, which includes all submodules.

    Returns:
        list[str]: A list of submodule names that satisfy the predicate, or all
        submodule names if no predicate is provided.

    This function is useful for dynamically discovering submodules within
    a package, allowing for filtering based on specific criteria.
    """
    predicate = predicate or (lambda _: True)
    names = [name for name in iter_submodule_names(name) if predicate(name)]
    names.sort(key=lambda x: [not is_package(x), x.replace("_", "~")])
    return names


module_cache: dict[str, float] = {}


def is_module_cache_dirty(name: str) -> bool:
    """Return True if the module cache is dirty.

    This function checks if the cache for the specified module is outdated
    by comparing the last modified time of the module's source file with
    the cached modification time stored in `module_cache`. If the module
    cannot be found or if there is no cached modification time, it determines
    whether the cache is considered dirty.

    Args:
        name (str): The name of the module to check for cache status.

    Returns:
        bool: True if the module cache is dirty (i.e., the module has been modified
        since it was last cached), otherwise False.

    This function is useful for ensuring that the cached data for a module
    is up-to-date, which can help prevent stale data from being used in
    applications that rely on dynamic module loading.
    """
    if not (path := get_module_path(name)):
        return False

    if not (mtime := module_cache.get(name)):
        return True

    return mtime != path.stat().st_mtime


@cache
def get_module_node_source(name: str) -> tuple[ast.Module, str] | None:
    """Return the AST node and source code of the specified module.

    This function attempts to retrieve the source code of a module given its
    name. If the module is found on the filesystem, it reads the source code
    directly from the file. If the module is not found, it tries to import the
    module and retrieve the source code using the `inspect` module. The function
    returns a tuple containing the parsed Abstract Syntax Tree (AST) node and
    the source code as a string. If the module cannot be found or the source
    code cannot be retrieved, it returns None.

    Args:
        name (str): The name of the module whose AST node and source code are
        to be retrieved.

    Returns:
        tuple[ast.Module, str] | None: A tuple containing the AST node and
        source code of the module, or None if the module cannot be found or
        the source code cannot be retrieved.

    Examples:
        >>> node, source = get_module_node_source("os")
        >>> isinstance(node, ast.Module)
        True
        >>> isinstance(source, str)
        True

        >>> get_module_node_source("non_existent_module") is None
        True

    This function is useful for dynamically analyzing the structure of modules
    and their source code, which can be helpful for documentation generation,
    code analysis, or introspection.
    """
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
    """Return the AST node of the specified module.

    This function retrieves the Abstract Syntax Tree (AST) node for a module
    given its name. It calls the `get_module_node_source` function to obtain
    the AST node and source code. If the module is found, it returns the AST
    node; otherwise, it returns None.

    Args:
        name (str): The name of the module whose AST node is to be retrieved.

    Returns:
        ast.Module | None: The AST node of the module, or None if the module
        cannot be found.

    Examples:
        >>> node = get_module_node("collections")
        >>> isinstance(node, ast.Module)
        True

        >>> get_module_node("non_existent_module") is None
        True

    This function is useful for obtaining the structure of a module for
    analysis, documentation generation, or introspection.
    """
    if node_source := get_module_node_source(name):
        return node_source[0]

    return None


def get_module_source(name: str) -> str | None:
    """Return the source code of the specified module.

    This function retrieves the source code of a module given its name.
    It calls the `get_module_node_source` function to obtain the Abstract
    Syntax Tree (AST) node and source code. If the module is found, it returns
    the source code; otherwise, it returns None.

    Args:
        name (str): The name of the module whose source code is to be retrieved.

    Returns:
        str | None: The source code of the module as a string, or None if
        the module cannot be found.

    Examples:
        >>> source = get_module_source("tempfile")
        >>> isinstance(source, str)
        True

        >>> get_module_source("non_existent_module") is None
        True

    This function is useful for dynamically accessing the source code of
    modules, which can be helpful for documentation generation, code analysis,
    or introspection.
    """
    if node_source := get_module_node_source(name):
        return node_source[1]

    return None


def iter_attribute_names(name: str, *, reverse: bool = False) -> Iterator[str]:
    """Yield parent module names in a dot-separated format.

    This function generates the names of parent modules for a given
    dot-separated module name. It can yield the names in either
    ascending or descending order based on the `reverse` flag. If
    `reverse` is set to True, it yields from the full name down to
    the top-level module; otherwise, it yields from the top-level
    module down to the full name.

    Args:
        name (str): The dot-separated name of the module for which to yield
        parent module names.
        reverse (bool, optional): If True, yields names from the full name
        to the top-level module. Defaults to False.

    Yields:
        Iterator[str]: The parent module names in dot-separated format.

    Examples:
        >>> list(iter_attribute_names("a.b.c.d"))
        ['a', 'a.b', 'a.b.c', 'a.b.c.d']
        >>> list(iter_attribute_names("a.b.c.d", reverse=True))
        ['a.b.c.d', 'a.b.c', 'a.b', 'a']

    This function is useful for module introspection and for generating
    hierarchical representations of module names.
    """
    names = name.split(".")
    it = range(len(names), 0, -1) if reverse else range(1, len(names) + 1)
    for k in it:
        yield ".".join(names[:k])


T = TypeVar("T")


def _is_equal(item, name: str, attr: str = "name") -> bool:
    return getattr(item, attr) == name


def iter_by_name(items: Iterable[T], name: str, attr: str = "name") -> Iterator[T]:
    """Yield items from the iterable that match the specified name.

    This function iterates over a collection of items and yields those
    that have a specified attribute equal to the given name. The attribute
    to compare can be specified using the `attr` parameter, which defaults
    to "name".

    Args:
        items (Iterable[T]): The collection of items to iterate over.
        name (str): The name to match against the specified attribute.
        attr (str, optional): The attribute of the items to compare with the
            name. Defaults to "name".

    Yields:
        T: The items that match the specified name.

    This function is useful for filtering items based on a specific
    attribute, allowing for easy retrieval of matching elements from
    a collection.
    """
    for item in items:
        if _is_equal(item, name, attr):
            yield item


def find_item_by_name(
    items: Iterable[T], name: str | Iterable[str], attr: str = "name"
) -> T | None:
    """Find the first item with a specified name from an iterable of items.

    This function searches through a collection of items and returns the
    first item that matches the specified name. If multiple names are
    provided, it will return the first matching item found. The attribute
    to compare can be specified using the `attr` parameter, which defaults
    to "name". If the name is not a string, it will iterate through the
    provided names and return the first matching item found.

    Args:
        items (Iterable[T]): The collection of items to search through.
        name (str | Iterable[str]): The name or names to match against the
            specified attribute.
        attr (str, optional): The attribute of the items to compare with the
            name. Defaults to "name".

    Returns:
        T | None: The first item that matches the specified name, or None
        if no matching item is found.

    This function is useful for retrieving specific items from a collection
    based on their attributes, facilitating easier access to desired elements.
    """
    if not isinstance(name, str):
        for name_ in name:
            if item := find_item_by_name(items, name_):
                return item

        return None

    for item in iter_by_name(items, name, attr):
        return item

    return None


def find_item_by_kind(items: Iterable[T], kind: str) -> T | None:
    """Find the first item of a specified kind from an iterable of items.

    This function searches through a collection of items and returns the
    first item that matches the specified kind. It uses the `iter_by_name`
    function to filter items based on the "kind" attribute.

    Args:
        items (Iterable[T]): The collection of items to search through.
        kind (str): The kind to match against the specified attribute.

    Returns:
        T | None: The first item that matches the specified kind, or None
        if no matching item is found.

    This function is useful for retrieving specific items from a collection
    based on their kind, facilitating easier access to desired elements.
    """
    for item in iter_by_name(items, kind, attr="kind"):
        return item

    return None


def find_item_by_type(items: Iterable, type_: type[T]) -> T | None:
    """Find the first item of a specified type from an iterable of items.

    This function searches through a collection of items and returns the
    first item that is an instance of the specified type. If no item of
    the specified type is found, it returns None.

    Args:
        items (Iterable): The collection of items to search through.
        type_ (type[T]): The type to match against the items.

    Returns:
        T | None: The first item that matches the specified type, or None
        if no matching item is found.

    This function is useful for retrieving specific items from a collection
    based on their type, facilitating easier access to desired elements.
    """
    for item in items:
        if isinstance(item, type_):
            return item

    return None


def delete_item_by_name(items: list[T], name: str, attr: str = "name") -> None:
    """Delete the first item with a specified name from a list of items.

    This function iterates through the provided list of items and deletes
    the first item that matches the specified name based on the given
    attribute. The deletion is performed in-place, modifying the original
    list.

    Args:
        items (list[T]): The list of items from which to delete the matching item.
        name (str): The name to match against the specified attribute of the items.
        attr (str, optional): The attribute of the items to compare with the
            name. Defaults to "name".

    Returns:
        None: This function does not return any value.

    This function is useful for removing specific items from a list based
    on their attributes, facilitating easier management of collections.
    """
    for k, item in enumerate(items):
        if _is_equal(item, name, attr):
            del items[k]
            return


def merge_unique_names(a: Iterable, b: Iterable, attr: str = "name") -> list[str]:
    """Merge two iterables and return a list of unique names.

    This function takes two iterables and collects the names of their
    elements, ensuring that the resulting list contains only unique names.
    The names are extracted from the specified attribute of each element,
    which defaults to "name". If an element's name is already in the
    resulting list, it will not be added again.

    Args:
        a (Iterable): The first iterable from which to collect names.
        b (Iterable): The second iterable from which to collect names.
        attr (str, optional): The attribute of the items to extract names from.
            Defaults to "name".

    Returns:
        list[str]: A list of unique names collected from both iterables.

    This function is useful for combining names from different sources while
    avoiding duplicates, facilitating easier management of collections.
    """
    names = [getattr(x, attr) for x in a]
    for x in b:
        if (name := getattr(x, attr)) not in names:
            names.append(name)

    return names


def split_filters(name: str) -> tuple[str, list[str]]:
    """Split filters written after `|` in a given string.

    This function takes a string that may contain filters separated by
    the `|` character and splits it into a base name and a list of filters.
    If no filters are present, it returns the original string as the base name
    and an empty list.

    Args:
        name (str): The input string containing the base name and optional filters.

    Returns:
        tuple[str, list[str]]: A tuple where the first element is the base name
        and the second element is a list of filters extracted from the input string.

    Examples:
        >>> split_filters("a.b.c")
        ('a.b.c', [])
        >>> split_filters("a.b.c|upper|strict")
        ('a.b.c', ['upper', 'strict'])
        >>> split_filters("|upper|strict")
        ('', ['upper', 'strict'])
        >>> split_filters("")
        ('', [])

    This function is useful for parsing strings that include filters, allowing
    for easy extraction of the main name and associated modifications.
    """
    index = name.find("|")
    if index == -1:
        return name, []

    name, filters = name[:index], name[index + 1 :]
    return name, filters.split("|")


def update_filters(org: list[str], update: list[str]) -> list[str]:
    """Update filters by merging and resolving conflicts.

    This function takes two lists of filters: the original list (`org`) and
    the list of updates (`update`). It merges these lists while ensuring that
    certain conflicting filters are resolved. Specifically, if both a lower
    and upper case filter or both long and short filters are present, the
    function will remove one of them based on the specified rules.

    Args:
        org (list[str]): The original list of filters.
        update (list[str]): The list of filters to update or add.

    Returns:
        list[str]: A new list of filters that combines the original and updated
        filters, with conflicts resolved.

    Examples:
        >>> update_filters(["upper"], ["lower"])
        ['lower']
        >>> update_filters(["lower"], ["upper"])
        ['upper']
        >>> update_filters(["long"], ["short"])
        ['short']
        >>> update_filters(["short"], ["long"])
        ['long']

    This function is useful for managing filter lists where certain filters
    may conflict, allowing for a clean and updated set of filters.
    """
    filters = org + update
    for x, y in [["lower", "upper"], ["long", "short"]]:
        if x in org and y in update:
            del filters[filters.index(x)]

        if y in org and x in update:
            del filters[filters.index(y)]

    return filters


def is_identifier(name: str) -> bool:
    """Return True if the name is a valid identifier, considering dot-separated parts.

    This function checks if the provided name is a valid Python identifier,
    which can include multiple parts separated by dots. Each part must be a
    valid identifier according to Python's naming rules. An identifier is
    a non-empty string that starts with a letter or underscore and can
    contain letters, digits, and underscores.

    Args:
        name (str): The name to check for validity as an identifier. This
        can be a single identifier or a dot-separated string of identifiers.

    Returns:
        bool: True if the name is a valid identifier (or identifiers) with
        dots, otherwise False.

    Examples:
        >>> is_identifier("valid_identifier")
        True
        >>> is_identifier("valid.identifier")
        True
        >>> is_identifier("invalid-identifier")
        False
        >>> is_identifier("1invalid")
        False
        >>> is_identifier("")
        False
        >>> is_identifier("valid.identifier.with.dots")
        True

    This function is useful for validating names in contexts where Python
    identifiers are required, such as variable names, function names, or
    module names.
    """
    return name != "" and all(x.isidentifier() for x in name.split("."))


def iter_identifiers(source: str) -> Iterator[tuple[str, bool]]:
    """Yield identifiers and their validity from the given source string.

    This function scans the provided source string and yields tuples of
    identifiers along with a boolean indicating whether each identifier
    is valid according to Python's naming rules. Identifiers can include
    dot-separated parts, and the function also handles quoted strings.

    Args:
        source (str): The input string from which to extract identifiers.

    Yields:
        Iterator[tuple[str, bool]]: A tuple where the first element is the
        identifier (or character) and the second element is a boolean that
        indicates whether the identifier is valid (True) or not (False).

    Examples:
        >>> list(iter_identifiers("valid_identifier"))
        [('valid_identifier', True)]
        >>> list(iter_identifiers("valid.identifier"))
        [('valid.identifier', True)]
        >>> list(iter_identifiers("invalid-identifier"))
        [('invalid', True), ('-', False), ('identifier', True)]
        >>> list(iter_identifiers("1invalid"))
        [('1', False), ('invalid', True)]
        >>> list(iter_identifiers('"quoted string"'))
        [('"quoted string"', False)]
        >>> list(iter_identifiers("a.b.c"))
        [('a.b.c', True)]

    This function is useful for parsing code or text where identifiers
    need to be validated, such as in code analysis, documentation generation,
    or syntax highlighting.
    """
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
def list_exported_names(module: str) -> list[str]:
    """Retrieve the list of exported names from a specified module.

    This function attempts to import the given module and access its
    `__all__` attribute, which is a list or tuple of names that should
    be considered public and exported when using `from module import *`.
    If the module cannot be found, or if the `__all__` attribute is not
    defined, an empty list is returned.

    Args:
        module (str): The name of the module from which to retrieve
        the exported names.

    Returns:
        list[str]: A list of exported names from the module, or an
        empty list if the module does not exist or has no exported names.

    Examples:
        >>> names = list_exported_names("pathlib")
        >>> all(x in names for x in ["PurePath", "Path", "PosixPath", "WindowsPath"])
        True

        >>> list_exported_names("non_existent_module")
        []

    This function is useful for dynamically discovering the public API
    of a module, allowing for better introspection and documentation
    generation.
    """
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
    """Retrieve an object from a specified module by its name.

    This function attempts to import the given module and then looks for
    the specified object within that module. The object can be nested,
    indicated by dot notation in the `name` parameter. If the module
    cannot be found or the object does not exist, None is returned.

    Args:
        name (str): The name of the object to retrieve, which can include
        dot notation for nested objects (e.g., "Class.method").
        module (str): The name of the module from which to retrieve the object.

    Returns:
        object | None: The requested object if found, or None if the module
        does not exist or the object cannot be found.

    Examples:
        >>> obj = get_object_from_module("Template", "jinja2")
        >>> obj.__module__, obj.__name__
        ('jinja2.environment', 'Template')

        >>> non_existent = get_object_from_module("NonExistent", "my_module")
        >>> non_existent is None
        True

    This function is useful for dynamic object retrieval in scenarios
    where the module and object names are determined at runtime.
    """
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
    """Check if the specified object is a dataclass.

    This function retrieves an object from the specified module using its
    name and checks if it is a dataclass. A dataclass is a class that is
    decorated with the `@dataclass` decorator from the `dataclasses` module.

    Args:
        name (str): The name of the object to check.
        module (str): The name of the module from which to retrieve the object.

    Returns:
        bool: True if the object is a dataclass, otherwise False.

    Examples:
        >>> from mkapi.doc import Item
        >>> is_dataclass("Item", "mkapi.doc")
        True

        >>> is_dataclass("is_dataclass", "mkapi.utils")
        False

    This function is useful for dynamically checking the nature of classes
    in a module, particularly when working with dataclasses.
    """
    obj = get_object_from_module(name, module)
    return dataclasses.is_dataclass(obj)


@cache
def get_base_classes(name: str, module: str) -> list[tuple[str, str]]:
    """Retrieve the base classes of a specified class from a module.

    This function attempts to retrieve an object from the specified module
    using its name and checks if it is a class. If it is a class, the function
    collects its base classes, excluding those from the built-in module.
    Each base class is returned as a tuple containing the base class name
    and its module.

    Args:
        name (str): The name of the class whose base classes are to be retrieved.
        module (str): The name of the module from which to retrieve the class.

    Returns:
        list[tuple[str, str]]: A list of tuples, where each tuple contains the
        name and module of a base class. If the specified class does not exist
        or is not a class, an empty list is returned.

    Examples:
        >>> base_classes = get_base_classes("Doc", "mkapi.doc")
        >>> base_classes
        [('Item', 'mkapi.doc')]

        >>> base_classes = get_base_classes("NonExistentClass", "my_module")
        >>> base_classes
        []

    This function is useful for understanding the inheritance hierarchy of
    classes in a module, particularly in dynamic analysis or introspection.
    """
    obj = get_object_from_module(name, module)

    bases = []

    if inspect.isclass(obj):
        for base in obj.__bases__:
            if base.__module__ != "builtins":
                basename = next(iter_identifiers(base.__name__))[0]
                bases.append((basename, base.__module__))

    return bases


@cache
def split_module_name(name: str) -> tuple[str, str | None] | None:
    """Split a dot-separated name into a module name and the remaining part.

    This function takes a dot-separated name and iterates through its
    components to determine the module name and the remaining part of the
    name. If a valid module is found, it returns the remaining name after
    the last valid module name. If the entire name corresponds to a valid
    module, it returns the module name and None. If the name belongs to a
    member of a module, it returns the member name and the module name.
    If no valid module is found, it returns None.

    Args:
        name (str): The dot-separated name to be split.

    Returns:
        tuple[str, str | None] | None: A tuple containing the remaining part
        of the name and the module name if a valid module is found. If the
        entire name corresponds to a valid module, it returns (module, None).
        If the name belongs to a member of a module, it returns (member name, module name).
        If no valid module is found and no previous module was identified,
        None is returned.

    Examples:
        'Section' is a member of 'mkapi.doc'

        >>> split_module_name("mkapi.doc.Section")
        ('Section', 'mkapi.doc')

        Entire name is a valid module

        >>> split_module_name("mkapi.doc")
        ('mkapi.doc', None)

        >>> split_module_name("invalid.module") is None
        True

    This function is useful for parsing names in contexts where modules
    and their attributes are represented in a dot-separated format.
    """
    modulename = None
    for module in iter_attribute_names(name):
        if not get_module_node(module):
            if not modulename:
                return None

            return name[len(modulename) + 1 :], modulename

        modulename = module

    return name, None
