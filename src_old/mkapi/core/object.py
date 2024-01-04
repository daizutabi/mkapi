"""Utility functions relating to object."""
import abc
import importlib
import inspect
from typing import Any


def get_object(name: str) -> Any:  # noqa: ANN401
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
    msg = f"Could not find object: {name}"
    raise ValueError(msg)


def get_fullname(obj: object, name: str) -> str:
    """Reutrns an object full name specified by `name`.

    Args:
        obj: Object that has a module.
        name: Object name in the module.

    Examples:
        >>> obj = get_object("mkapi.core.base.Item")
        >>> get_fullname(obj, "Section")
        'mkapi.core.base.Section'
        >>> get_fullname(obj, "add_fence")
        'mkapi.core.preprocess.add_fence'
        >>> get_fullname(obj, 'abc')
        ''
    """
    obj = inspect.getmodule(obj)
    for name_ in name.split("."):
        if not hasattr(obj, name_):
            return ""
        obj = getattr(obj, name_)

    if isinstance(obj, property):
        return ""

    return ".".join(split_prefix_and_name(obj))


def split_prefix_and_name(obj: object) -> tuple[str, str]:
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
            prefix = f"{module}.{prefix}"
        if prefix == "__main__":
            prefix = ""
    return prefix, name


def get_qualname(obj: object) -> str:
    """Return `qualname`."""
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__
    return ""


def get_sourcefile_and_lineno(obj: type) -> tuple[str, int]:
    """Return source file and line number."""
    try:
        sourcefile = inspect.getsourcefile(obj) or ""
    except TypeError:
        sourcefile = ""
    try:
        _, lineno = inspect.getsourcelines(obj)
    except (TypeError, OSError):
        lineno = -1
    return sourcefile, lineno


# Issue#19 (metaclass). TypeError: descriptor 'mro' of 'type' object needs an argument.
def get_mro(obj: Any) -> list[type]:  # noqa: D103, ANN401
    try:
        objs = obj.mro()[:-1]  # drop ['object']
    except TypeError:
        objs = obj.mro(obj)[:-2]  # drop ['type', 'object']
    if objs[-1] == abc.ABC:
        objs = objs[:-1]
    return objs


def get_sourcefiles(obj: object) -> list[str]:
    """Returns a list of source file.

    If `obj` is a class, source files of its superclasses are also included.

    Args:
        obj: Object name.
    """
    objs = get_mro(obj) if inspect.isclass(obj) and hasattr(obj, "mro") else [obj]
    sourfiles = []
    for obj in objs:
        try:
            sourcefile = inspect.getsourcefile(obj) or ""  # type: ignore
        except TypeError:
            pass
        else:
            if sourcefile:
                sourfiles.append(sourcefile)
    return sourfiles


def from_object(obj: object) -> bool:
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


def get_origin(obj):  # noqa: ANN001, ANN201
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
    try:
        wrapped = obj.__wrapped__
    except AttributeError:
        pass
    else:
        return get_origin(wrapped)
    try:
        wrapped = obj.__pytest_wrapped__
    except AttributeError:
        pass
    else:
        return get_origin(wrapped.obj)

    return obj
