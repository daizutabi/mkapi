"""This module provides utility functions that relates to object."""
import importlib
import inspect
from functools import partial
from typing import Any, Callable, List, Tuple


def get_object(name: str) -> Any:
    """Reutrns an object specified by `name`.

    Args:
        name: Object name.

    Examples:
        >>> import inspect
        >>> obj = get_object('mkapi.core')
        >>> inspect.ismodule(obj)
        True
        >>> obj = get_object('mkapi.core.base')
        >>> inspect.ismodule(obj)
        True
        >>> obj = get_object('mkapi.core.node.Node')
        >>> inspect.isclass(obj)
        True
        >>> obj = get_object('mkapi.core.node.Node.get_markdown')
        >>> inspect.isfunction(obj)
        True
    """
    names = name.split(".")
    for k in range(len(names), 0, -1):
        module_name = ".".join(names[:k])
        try:
            obj = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        for attr in names[k:]:
            obj = getattr(obj, attr)
        return obj
    raise ValueError(f"Could not find object: {name}")


def get_fullname(obj: Any, name: str) -> str:
    """Reutrns an object full name specified by `name`.

    Args:
        obj: Object that has a module.
        name: Object name in the module.

    Examples:
        >>> import inspect
        >>> obj = get_object('mkapi.core.base.Item')
        >>> get_fullname(obj, 'Section')
        'mkapi.core.base.Section'
        >>> get_fullname(obj, 'linker.link')
        'mkapi.core.linker.link'
        >>> get_fullname(obj, 'abc')
        ''
    """
    if not hasattr(obj, "__module__"):
        return ""
    obj = importlib.import_module(obj.__module__)
    names = name.split(".")

    for name in names:
        if not hasattr(obj, name):
            return ""
        obj = getattr(obj, name)

    return ".".join(split_prefix_and_name(obj))


def split_prefix_and_name(obj: Any) -> Tuple[str, str]:
    """Split an object full name into prefix and name.

    Args:
        obj: Object that has a module.

    Examples:
        >>> import inspect
        >>> obj = get_object('mkapi.core')
        >>> split_prefix_and_name(obj)
        ('mkapi', 'core')
        >>> obj = get_object('mkapi.core.base')
        >>> split_prefix_and_name(obj)
        ('mkapi.core', 'base')
        >>> obj = get_object('mkapi.core.node.Node')
        >>> split_prefix_and_name(obj)
        ('mkapi.core.node', 'Node')
        >>> obj = get_object('mkapi.core.node.Node.get_markdown')
        >>> split_prefix_and_name(obj)
        ('mkapi.core.node.Node', 'get_markdown')
    """
    if isinstance(obj, property):
        obj = obj.fget
    if inspect.ismodule(obj):
        prefix, _, name = obj.__name__.rpartition(".")
    else:
        module = obj.__module__
        qualname = obj.__qualname__
        if "." not in qualname:
            prefix, name = module, qualname
        else:
            prefix, _, name = qualname.rpartition(".")
            prefix = ".".join([module, prefix])
        if prefix == "__main__":
            prefix = ""
    return prefix, name


def get_qualname(obj: Any):
    if isinstance(obj, property):
        obj = obj.fget
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__
    return ""


def get_sourcefile_and_lineno(obj: Any) -> Tuple[str, int]:
    if isinstance(obj, property):
        obj = obj.fget
    try:
        sourcefile = inspect.getsourcefile(obj) or ""
    except TypeError:
        sourcefile = ""
    try:
        lineno = inspect.getsourcelines(obj)[1]
    except (TypeError, OSError):
        lineno = -1
    return sourcefile, lineno


def is_dunder(obj: Any, only_documented: bool = True) -> bool:
    """Returns dunder methods if they have a sourcefile.

    Args:
        obj: Object
    """
    if not hasattr(obj, "__name__"):
        return False
    name = obj.__name__
    if name == "__init__":
        return False
    elif name.startswith("__") and name.endswith("__"):
        try:
            inspect.getsource(obj)
        except TypeError:
            return False
        else:
            if not only_documented:
                return True
            else:
                return bool(inspect.getdoc(obj))
    return False


def get_dunders(obj: Any, only_documented: bool = True) -> List[Callable]:
    filter = partial(is_dunder, only_documented=only_documented)
    members = inspect.getmembers(obj, filter)
    return [obj for _, obj in members]
