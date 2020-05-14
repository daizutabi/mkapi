import importlib
import inspect
from dataclasses import dataclass, field
from typing import Any, List

from mkapi.core.docstring import Docstring, parse_docstring

ISFUNCTIONS = {}
for x in dir(inspect):
    if x.startswith("is"):
        name = x[2:]
        if name not in ["routine", "builtin", "code"]:
            ISFUNCTIONS[name] = getattr(inspect, x)


@dataclass
class Node:
    obj: Any = field(repr=False)
    name: str
    depth: int
    prefix: str
    kinds: List[str]
    lineno: int
    docstring: Docstring
    members: List["Node"]

    def __post_init__(self):
        self.kind = self.kinds[0]
        if self.name.startswith("__"):
            self.type = "special"
        elif self.name.startswith("_"):
            self.type = "private"
        else:
            self.type = "normal"


def get_kinds(obj) -> List[str]:
    kinds = []
    for kind, func in ISFUNCTIONS.items():
        if func(obj):
            kinds.append(kind)
    if isinstance(obj, property):
        if obj.fset:
            kinds.append("readwrite_property")
        else:
            kinds.append("readonly_property")
    return kinds


def get_lineno(obj) -> int:
    if isinstance(obj, property):
        obj = obj.fget
    return inspect.getsourcelines(obj)[1]


def filter(obj) -> bool:
    if not get_kinds(obj):
        return False
    try:
        get_lineno(obj)
    except TypeError:
        return False
    else:
        return True


def walk(name, obj, prefix="", depth=0) -> Node:
    kinds = get_kinds(obj)
    lineno = get_lineno(obj)
    docstring = parse_docstring(obj)
    if prefix:
        next_prefix = ".".join([prefix, name])
    else:
        next_prefix = name
    members = []
    if not isinstance(obj, property):
        for x in inspect.getmembers(obj, filter):
            member = walk(*x, prefix=next_prefix, depth=depth + 1)
            if member.type == "normal" or member.docstring:
                members.append(member)
        members.sort(key=lambda x: x.lineno)
    return Node(obj, name, depth, prefix, kinds, lineno, docstring, members)


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
    node = walk(name, obj)
    return node
