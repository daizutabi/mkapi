import importlib
import inspect
from functools import partial
from typing import Any, List, Tuple

from mkapi.core.base import Node
from mkapi.core.docstring import parse_docstring
from mkapi.core.inspect import get_signature

ISFUNCTIONS = {}
for x in dir(inspect):
    if x.startswith("is"):
        name = x[2:]
        if name not in ["routine", "builtin", "code"]:
            ISFUNCTIONS[name] = getattr(inspect, x)


def get_kinds(obj) -> List[str]:
    kinds = []
    for kind, func in ISFUNCTIONS.items():
        if func(obj):
            kinds.append(kind)
    return kinds


def get_kind(obj) -> str:
    if hasattr(obj, "__dataclass_fields__"):
        return "dataclass"
    if isinstance(obj, property):
        if obj.fset:
            return "readwrite_property"
        else:
            return "readonly_property"
    kinds = get_kinds(obj)
    if not kinds:
        return ""
    if "generatorfunction" in kinds:
        return "generator"
    if "function" in kinds:
        try:
            parameters = inspect.signature(obj).parameters
        except (ValueError, TypeError):
            return ""
        if parameters:
            arg = list(parameters)[0]
            if arg == "self":
                return "method"
    kind = kinds[-1]
    if kind == "module":
        sourcefile = inspect.getsourcefile(obj)
        if sourcefile and sourcefile.endswith("__init__.py"):
            kind = "package"
    return kind


def get_sourcefile_and_lineno(obj) -> Tuple[str, int]:
    if isinstance(obj, property):
        obj = obj.fget
    try:
        sourcefile = inspect.getsourcefile(obj) or ""
        lineno = inspect.getsourcelines(obj)[1]
    except (TypeError, OSError):
        return "", -1
    return sourcefile, lineno


def filter(obj, qualname, sourcefile="") -> bool:
    if isinstance(obj, property):
        return True
    kind = get_kind(obj)
    if kind == "":
        return False

    if kind == "dataclass" and not qualname:
        return True
    sourcefile_, _ = get_sourcefile_and_lineno(obj)
    if sourcefile_ == "" or (sourcefile and sourcefile != sourcefile_):
        return False
    if hasattr(obj, "__qualname__"):
        if not qualname:
            return True
        if obj.__qualname__.startswith(qualname):
            return True
    return False


def get_members(obj, kind, sourcefile, prefix, depth, max_depth=-1) -> List[Node]:
    if max_depth != -1 and depth > max_depth:
        return []
    if isinstance(obj, property):
        return []

    qualname = getattr(obj, "__qualname__", "")
    if kind in ["package", "module"]:
        func = partial(filter, qualname=qualname, sourcefile=sourcefile)
    else:
        func = partial(filter, qualname=qualname)

    members = []
    for x in inspect.getmembers(obj, func):
        if x[0].startswith("_"):
            continue
        member = walk(*x, prefix=prefix, depth=depth, max_depth=max_depth)
        if member.kind in ["class", "dataclass"] and not member.docstring:
            docstring = parse_docstring(x[1].__init__)
            if docstring:
                markdown = docstring.sections[0].markdown
                if not markdown.startswith("Initialize self"):
                    member.docstring = docstring
        if member.docstring:
            members.append(member)
    return sorted(members, key=lambda x: (x.sourcefile, x.lineno))


def walk(name, obj, prefix="", depth=0, max_depth=-1) -> Node:
    member_prefix = name
    if prefix:
        member_prefix = ".".join([prefix, member_prefix])
    kind = get_kind(obj)
    sourcefile, lineno = get_sourcefile_and_lineno(obj)
    signature = get_signature(obj)
    docstring = parse_docstring(obj)
    members = get_members(obj, kind, sourcefile, member_prefix, depth + 1, max_depth)

    node = Node(
        obj=obj,
        name=name,
        depth=depth,
        prefix=prefix,
        kind=kind,
        sourcefile=sourcefile,
        lineno=lineno,
        signature=signature,
        docstring=docstring,
        members=members,
    )
    if docstring and docstring.type:
        node.type = docstring.type
    return node


def get_attr(path: str):
    module_path, _, name = path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, name)


def get_object(name: str):
    try:
        return get_attr(name)
    except (ModuleNotFoundError, AttributeError, ValueError):
        return importlib.import_module(name)


def get_node(name: Any, max_depth: int = -1, headless: bool = False) -> Node:
    if isinstance(name, str):
        obj = get_object(name)
    else:
        obj = name
    node = walk(name, obj, max_depth=max_depth)
    node.headless = headless
    return node
