import importlib
from typing import Any, List


def get_indent(line: str) -> int:
    indent = 0
    for x in line:
        if x != " ":
            return indent
        indent += 1
    return -1


def join(lines):
    indent = get_indent(lines[0])
    return "\n".join(line[indent:] for line in lines).strip()


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


def split_filters(name):
    """
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


def update_filters(org: List[str], update: List[str]) -> List[str]:
    """
    Examples:
        >>> update_filters(['upper'], ['lower'])
        ['lower']
        >>> update_filters(['lower'], ['upper'])
        ['upper']
        >>> update_filters(['long'], ['short'])
        ['short']
        >>> update_filters(['short'], ['long'])
        ['long']
    """
    filters = org + update
    for x, y in [["lower", "upper"], ["long", "short"]]:
        if x in org and y in update:
            del filters[filters.index(x)]
        if y in org and x in update:
            del filters[filters.index(y)]

    return filters
