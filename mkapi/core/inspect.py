import importlib
import inspect
from dataclasses import dataclass, field
from typing import Any, List, Optional

ISFUNCTIONS = {}
for x in dir(inspect):
    if x.startswith("is"):
        name = x[2:]
        if name not in ["routine", "builtin"]:
            ISFUNCTIONS[name] = getattr(inspect, x)

IGNORE_NAMES = ["__weakref__"]


@dataclass
class Node:
    obj: Any = field(repr=False)
    name: str
    depth: int
    prefix: str
    kinds: List[str]
    docstring: Optional[str]
    members: List["Node"]


def get_kinds(obj):
    kinds = []
    for kind, func in ISFUNCTIONS.items():
        if func(obj):
            kinds.append(kind)
    return kinds


def get_members(obj):
    qualname = getattr(obj, "__qualname__", "")
    for _, value in inspect.getmembers(obj):
        if not hasattr(value, "__qualname__"):
            continue
        if not qualname or value.__qualname__.startswith(qualname):
            yield value


def walk(obj, prefix="", depth=0):
    name = obj.__name__
    if name in IGNORE_NAMES:
        return None
    kinds = get_kinds(obj)
    if not kinds:
        return None
    docstring = inspect.getdoc(obj)
    members = []
    if prefix:
        next_prefix = ".".join([prefix, name])
    else:
        next_prefix = name
    for member in get_members(obj):
        member = walk(member, prefix=next_prefix, depth=depth + 1)
        if member:
            members.append(member)
    return Node(obj, name, depth, prefix, kinds, docstring, members)


def get_attr(path: str):
    module_path, _, name = path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, name)


def get_object(name: str):
    try:
        return get_attr(name)
    except (ModuleNotFoundError, AttributeError):
        return importlib.import_module(name)


def get_node(name: str) -> Node:
    obj = get_object(name)
    node = walk(obj)
    return node
