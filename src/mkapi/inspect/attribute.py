"""Functions that inspect attributes from source code."""
from __future__ import annotations

import _ast
import ast
import dataclasses
import importlib
import inspect
from ast import AST
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, TypeGuard

from mkapi.core.preprocess import join_without_indent

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from types import ModuleType

    from _typeshed import DataclassInstance


def parse_attribute(x) -> str:
    return ".".join([parse_node(x.value), x.attr])


def parse_attribute_with_lineno(x) -> tuple[str, int]:
    return parse_node(x), x.lineno


def parse_subscript(x) -> str:
    value = parse_node(x.value)
    slice = parse_node(x.slice)
    if isinstance(slice, str):
        return f"{value}[{slice}]"

    type_str = ", ".join([str(elt) for elt in slice])
    return f"{value}[{type_str}]"


def parse_tuple(x):
    return tuple(parse_node(x) for x in x.elts)


def parse_list(x):
    return "[" + ", ".join(parse_node(x) for x in x.elts) + "]"


def parse_node(x):
    if isinstance(x, _ast.Name):
        return x.id
    elif isinstance(x, _ast.Assign):
        return parse_node(x.targets[0])
    elif isinstance(x, _ast.Attribute):
        return parse_attribute(x)
    elif isinstance(x, _ast.Subscript):
        return parse_subscript(x)
    elif isinstance(x, _ast.Tuple):
        return parse_tuple(x)
    elif isinstance(x, _ast.List):
        return parse_list(x)
    elif hasattr(_ast, "Constant") and isinstance(x, _ast.Constant):
        return x.value
    elif hasattr(_ast, "Index") and isinstance(x, _ast.Index):
        return x.value
    elif hasattr(_ast, "Ellipsis") and isinstance(x, _ast.Ellipsis):
        return x.value
    elif hasattr(_ast, "Str") and isinstance(x, _ast.Str):
        return x.s
    else:
        raise NotImplementedError


def parse_annotation_assign(assign) -> tuple[str, int, str]:
    type = parse_node(assign.annotation)
    attr, lineno = parse_attribute_with_lineno(assign.target)
    return attr, lineno, type


def get_description(lines: list[str], lineno: int) -> str:
    index = lineno - 1
    line = lines[index]
    if "  #: " in line:
        return line.split("  #: ")[1].strip()
    if index != 0:
        line = lines[index - 1].strip()
        if line.startswith("#: "):
            return line[3:].strip()
    if index + 1 < len(lines):
        docs = []
        in_doc = False
        for line in lines[index + 1 :]:
            line = line.strip()
            if not in_doc and not line:
                break
            elif not in_doc and (line.startswith("'''") or line.startswith('"""')):
                mark = line[:3]
                if line.endswith(mark):
                    return line[3:-3]
                in_doc = True
                docs.append(line[3:])
            elif in_doc and line.endswith(mark):
                docs.append(line[:-3])
                return "\n".join(docs).strip()
            elif in_doc:
                docs.append(line)
    return ""


def get_source(obj) -> str:  # noqa: ANN001
    """Return the text of the source code for an object without exception."""
    try:
        return inspect.getsource(obj)
    except OSError:
        return ""


def get_attributes_with_lineno(
    nodes: Iterable[AST],
    module: ModuleType,
    *,
    is_module: bool = False,
) -> list[tuple[str, int, Any]]:
    attr_dict: dict[tuple[str, int], Any] = {}
    linenos: dict[int, int] = {}

    def update(attr, lineno, type):
        if type or (attr, lineno) not in attr_dict:
            attr_dict[(attr, lineno)] = type
            linenos[lineno] = linenos.get(lineno, 0) + 1

    globals = dict(inspect.getmembers(module))
    for x in nodes:
        if isinstance(x, _ast.AnnAssign):
            attr, lineno, type_str = parse_annotation_assign(x)
            try:
                type = eval(type_str, globals)
            except NameError:
                type = type_str
            update(attr, lineno, type)
        if isinstance(x, _ast.Attribute) and isinstance(x.ctx, _ast.Store):
            attr, lineno = parse_attribute_with_lineno(x)
            update(attr, lineno, ())
        if is_module and isinstance(x, _ast.Assign):
            attr, lineno = parse_attribute_with_lineno(x)
            update(attr, lineno, ())
    attr_lineno = [(attr, lineno, type) for (attr, lineno), type in attr_dict.items()]
    attr_lineno = [x for x in attr_lineno if linenos[x[1]] == 1]
    attr_lineno = sorted(attr_lineno, key=lambda x: x[1])
    return attr_lineno


def get_attributes_dict(
    attr_list: list[tuple[str, int, Any]],
    source: str,
    prefix: str = "",
) -> dict[str, tuple[Any, str]]:
    attrs: dict[str, tuple[Any, str]] = {}
    lines = source.split("\n")
    for k, (name, lineno, type) in enumerate(attr_list):
        if not prefix or name.startswith(prefix):
            name = name[len(prefix) :]
            stop = len(lines)
            if k < len(attr_list) - 1:
                stop = attr_list[k + 1][1] - 1
            description = get_description(lines[:stop], lineno)
            if type:
                attrs[name] = type, description  # Assignment with type annotation wins.
            elif name not in attrs:
                attrs[name] = None, description
    return attrs


def get_class_attributes(cls: type[Any]) -> dict[str, tuple[Any, str]]:
    """Return a dictionary that maps attribute name to a tuple of (type, description).

    Args:
        cls: Class object.

    Examples:
        >>> from mkapi.core.base import Base
        >>> attrs = get_class_attributes(Base)
        >>> attrs["name"][0] is str
        True
        >>> attrs["name"][1]
        'Name of self.'
        >>> attrs["callback"][0]
        True
    """
    source = get_source(cls)
    if not source:
        return {}
    source = join_without_indent(source.split("\n"))
    node = ast.parse(source)
    nodes = ast.walk(node)
    module = importlib.import_module(cls.__module__)
    attr_lineno = get_attributes_with_lineno(nodes, module)
    return get_attributes_dict(attr_lineno, source, prefix="self.")


def get_dataclass_attributes(
    cls: type[DataclassInstance],
) -> dict[str, tuple[Any, str]]:
    """Return a dictionary that maps attribute name to a tuple of (type, description).

    Args:
        cls: Dataclass object.

    Examples:
        >>> from mkapi.core.base import Item, Type, Inline
        >>> attrs = get_dataclass_attributes(Item)
        >>> attrs["type"][0] is Type
        True
        >>> attrs["description"][0] is Inline
        True
    """
    attrs = {}
    for field in dataclasses.fields(cls):
        if field.type != dataclasses.InitVar:
            attrs[field.name] = field.type, ""

    source = get_source(cls)
    source = join_without_indent(source.split("\n"))
    if not source:
        return {}
    node = ast.parse(source).body[0]

    def nodes() -> Iterator[AST]:
        for x in ast.iter_child_nodes(node):
            if isinstance(x, _ast.FunctionDef):
                break
            yield x

    module = importlib.import_module(cls.__module__)
    attr_lineno = get_attributes_with_lineno(nodes(), module)
    for name, (type_, description) in get_attributes_dict(attr_lineno, source).items():
        if name in attrs:
            attrs[name] = attrs[name][0], description
        else:
            attrs[name] = type_, description

    return attrs


def get_module_attributes(module: ModuleType) -> dict[str, tuple[Any, str]]:
    """Return a dictionary that maps attribute name to a tuple of (type, description).

    Args:
        module: Module object.

    Examples:
        >>> from mkapi.core import renderer
        >>> attrs = get_module_attributes(renderer)
        >>> attrs["renderer"][0] is renderer.Renderer
        True
    """
    source = get_source(module)
    if not source:
        return {}
    node = ast.parse(source)
    nodes = ast.iter_child_nodes(node)
    attr_lineno = get_attributes_with_lineno(nodes, module, is_module=True)
    return get_attributes_dict(attr_lineno, source)


def isdataclass(obj: object) -> TypeGuard[type[DataclassInstance]]:
    """Return True if obj is a dataclass."""
    return dataclasses.is_dataclass(obj) and isinstance(obj, type)


ATTRIBUTES_FUNCTIONS = [
    (isdataclass, get_dataclass_attributes),
    (inspect.isclass, get_class_attributes),
    (inspect.ismodule, get_module_attributes),
]


@lru_cache(maxsize=1000)
def get_attributes(obj: object) -> dict[str, tuple[Any, str]]:
    """Return a dictionary that maps attribute name to a tuple of (type, description).

    Args:
        obj: Object.

    See Also:
        get_class_attributes_, get_dataclass_attributes_, get_module_attributes_.
    """
    for is_, get in ATTRIBUTES_FUNCTIONS:
        if is_(obj):
            return get(obj)
    return {}
