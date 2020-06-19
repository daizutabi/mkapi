"""This module provides utility functions that relate to object."""
import importlib
import inspect
from typing import Any, List, Tuple


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
        >>> obj = get_object('mkapi.core.base.Item')
        >>> get_fullname(obj, 'Section')
        'mkapi.core.base.Section'
        >>> get_fullname(obj, 'preprocess')
        'mkapi.core.preprocess'
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
    """Splits an object full name into prefix and name.

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
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__
    return ""


def get_sourcefile_and_lineno(obj: Any) -> Tuple[str, int]:
    try:
        sourcefile = inspect.getsourcefile(obj) or ""
    except TypeError:
        sourcefile = ""
    try:
        lineno = inspect.getsourcelines(obj)[1]
    except (TypeError, OSError):
        lineno = -1
    return sourcefile, lineno


def get_sourcefiles(obj: Any) -> List[str]:
    """Returns a list of source file.

    If `obj` is a class, source files of its superclasses are also included.

    Args:
        obj: Object name.
    """
    if inspect.isclass(obj) and hasattr(obj, "mro"):
        objs = obj.mro()[:-1]
    else:
        objs = [obj]
    sourfiles = []
    for obj in objs:
        try:
            sourcefile = inspect.getsourcefile(obj) or ""
        except TypeError:
            pass
        else:
            if sourcefile:
                sourfiles.append(sourcefile)
    return sourfiles


def from_object(obj: Any) -> bool:
    """Returns True, if the docstring of `obj` is the same as that of `object`.

    Args:
        name: Object name.
        obj: Object.

    Examples:
        >>> class A: pass
        >>> from_object(A.__call__)
        True
        >>> from_object(A.__eq__)
        True
        >>> from_object(A.__getattribute__)
        True
    """
    if not hasattr(obj, "__name__"):
        return False
    name = obj.__name__
    if not hasattr(object, name):
        return False
    return inspect.getdoc(obj) == getattr(object, name).__doc__


def get_origin(obj: Any) -> Any:
    """Returns an original object.

    Examples:
        >>> class A:
        ...    @property
        ...    def x(self):
        ...        pass
        >>> hasattr(A.x, __name__)
        False
        >>> get_origin(A.x).__name__
        'x'
    """
    if isinstance(obj, property):
        return get_origin(obj.fget)
    if not callable(obj):
        return obj
    if hasattr(obj, "__wrapped__"):
        return get_origin(obj.__wrapped__)
    if hasattr(obj, "__pytest_wrapped__"):
        return get_origin(obj.__pytest_wrapped__.obj)
    return obj
