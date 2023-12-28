"""Functions that inspect attributes from source code."""
from __future__ import annotations

import ast
import dataclasses
import inspect
from ast import AST
from functools import lru_cache
from typing import TYPE_CHECKING, Any, TypeGuard

from mkapi.core.preprocess import join_without_indent

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from types import ModuleType

    from _typeshed import DataclassInstance


def getsource_dedent(obj) -> str:  # noqa: ANN001
    """Return the text of the source code for an object without exception."""
    try:
        source = inspect.getsource(obj)
    except OSError:
        return ""
    return join_without_indent(source)


def parse_attribute(node: ast.Attribute) -> str:  # noqa: D103
    return ".".join([parse_node(node.value), node.attr])


def parse_subscript(node: ast.Subscript) -> str:  # noqa: D103
    value = parse_node(node.value)
    slice_ = parse_node(node.slice)
    return f"{value}[{slice_}]"


def parse_tuple(node: ast.Tuple) -> str:  # noqa: D103
    return ", ".join(parse_node(n) for n in node.elts)


def parse_list(node: ast.List) -> str:  # noqa: D103
    return "[" + ", ".join(parse_node(n) for n in node.elts) + "]"


PARSE_NODE_FUNCTIONS: list[tuple[type, Callable[..., str] | str]] = [
    (ast.Attribute, parse_attribute),
    (ast.Subscript, parse_subscript),
    (ast.Tuple, parse_tuple),
    (ast.List, parse_list),
    (ast.Name, "id"),
    (ast.Constant, "value"),
    (ast.Name, "value"),
    (ast.Ellipsis, "value"),
    (ast.Str, "value"),
]


def parse_node(node: AST) -> str:
    """Return a string expression for AST node."""
    for type_, parse in PARSE_NODE_FUNCTIONS:
        if isinstance(node, type_):
            if callable(parse):
                return parse(node)
            return getattr(node, parse)
    return ast.unparse(node)


def get_attribute_list(
    nodes: Iterable[AST],
    module: ModuleType,
    *,
    is_module: bool = False,
) -> list[tuple[str, int, Any]]:
    """Retrun list of tuple of (name, lineno, type)."""
    attr_dict: dict[tuple[str, int], Any] = {}
    linenos: dict[int, int] = {}

    def update(name, lineno, type_=()) -> None:  # noqa: ANN001
        if type_ or (name, lineno) not in attr_dict:
            attr_dict[(name, lineno)] = type_
            linenos[lineno] = linenos.get(lineno, 0) + 1

    members = dict(inspect.getmembers(module))
    for node in nodes:
        if isinstance(node, ast.AnnAssign):
            type_str = parse_node(node.annotation)
            type_ = members.get(type_str, type_str)
            update(parse_node(node.target), node.lineno, type_)
        elif isinstance(node, ast.Attribute):  # and isinstance(node.ctx, ast.Store):
            update(parse_node(node), node.lineno)
        elif is_module and isinstance(node, ast.Assign):
            update(parse_node(node.targets[0]), node.lineno)
    attrs = [(name, lineno, type_) for (name, lineno), type_ in attr_dict.items()]
    attrs = [attr for attr in attrs if linenos[attr[1]] == 1]
    return sorted(attrs, key=lambda attr: attr[1])


def get_description(lines: list[str], lineno: int) -> str:
    """Return description from lines of source."""
    index = lineno - 1
    line = lines[index]
    if "  #: " in (line := lines[lineno - 1]):
        return line.split("  #: ")[1].strip()
    if lineno > 1 and (line := lines[lineno - 2].strip()).startswith("#: "):
        return line[3:].strip()
    if lineno < len(lines):
        docs, in_doc, mark = [], False, ""
        for line_ in lines[lineno:]:
            line = line_.strip()
            if in_doc:
                if line.endswith(mark):
                    docs.append(line[:-3])
                    return "\n".join(docs).strip()
                docs.append(line)
            elif line.startswith(("'''", '"""')):
                in_doc, mark = True, line[:3]
                if line.endswith(mark):
                    return line[3:-3]
                docs.append(line[3:])
            elif not line:
                return ""
    return ""


def get_attribute_dict(
    attr_list: list[tuple[str, int, Any]],
    source: str,
    prefix: str = "",
) -> dict[str, tuple[Any, str]]:
    """Return an attribute dictionary."""
    attrs: dict[str, tuple[Any, str]] = {}
    lines = source.split("\n")
    for k, (name, lineno, type_) in enumerate(attr_list):
        if not name.startswith(prefix):
            continue
        name = name[len(prefix) :]  # noqa: PLW2901
        stop = attr_list[k + 1][1] - 1 if k < len(attr_list) - 1 else len(lines)
        description = get_description(lines[:stop], lineno)
        if type_:
            attrs[name] = (type_, description)  # Assignment with type wins.
        elif name not in attrs:
            attrs[name] = None, description
    return attrs


def _nodeiter_before_function(node: AST) -> Iterator[AST]:
    for x in ast.iter_child_nodes(node):
        if isinstance(x, ast.FunctionDef):
            break
        yield x


def get_dataclass_attributes(cls: type) -> dict[str, tuple[Any, str]]:
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
    source = getsource_dedent(cls)
    module = inspect.getmodule(cls)
    if not source or not module:
        return {}

    node = ast.parse(source).body[0]
    nodes = _nodeiter_before_function(node)
    attr_lineno = get_attribute_list(nodes, module)
    attr_dict = get_attribute_dict(attr_lineno, source)

    attrs: dict[str, tuple[Any, str]] = {}
    for field in dataclasses.fields(cls):
        if field.type != dataclasses.InitVar:
            attrs[field.name] = field.type, ""
    for name, (type_, description) in attr_dict.items():
        attrs[name] = attrs.get(name, [type_])[0], description

    return attrs


def get_class_attributes(cls: type) -> dict[str, tuple[Any, str]]:
    """Return a dictionary that maps attribute name to a tuple of (type, description).

    Args:
        cls: Class object.
    """
    source = getsource_dedent(cls)
    module = inspect.getmodule(cls)
    if not source or not module:
        return {}

    node = ast.parse(source)
    nodes = ast.walk(node)
    attr_lineno = get_attribute_list(nodes, module)
    return get_attribute_dict(attr_lineno, source, prefix="self.")


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
    source = getsource_dedent(module)
    if not source:
        return {}

    node = ast.parse(source)
    nodes = ast.iter_child_nodes(node)
    attr_lineno = get_attribute_list(nodes, module, is_module=True)
    return get_attribute_dict(attr_lineno, source)


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
