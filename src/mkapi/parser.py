"""Parser module."""
from __future__ import annotations

import ast
from ast import Attribute, Constant, List, Name, Subscript, Tuple
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ast import AST
    from collections.abc import Callable


def parse_attribute(node: Attribute) -> str:  # noqa: D103
    return ".".join([parse_node(node.value), node.attr])


def parse_subscript(node: Subscript) -> str:  # noqa: D103
    value = parse_node(node.value)
    slice_ = parse_node(node.slice)
    return f"{value}[{slice_}]"


def parse_constant(node: Constant) -> str:  # noqa: D103
    if node.value is Ellipsis:
        return "..."
    if isinstance(node.value, str):
        return node.value
    return parse_value(node.value)


def parse_list(node: List) -> str:  # noqa: D103
    return "[" + ", ".join(parse_node(n) for n in node.elts) + "]"


def parse_tuple(node: Tuple) -> str:  # noqa: D103
    return ", ".join(parse_node(n) for n in node.elts)


def parse_value(value: Any) -> str:  # noqa: D103, ANN401
    return str(value)


PARSE_NODE_FUNCTIONS: list[tuple[type, Callable[..., str] | str]] = [
    (Attribute, parse_attribute),
    (Subscript, parse_subscript),
    (Constant, parse_constant),
    (List, parse_list),
    (Tuple, parse_tuple),
    (Name, "id"),
]


def parse_node(node: AST) -> str:
    """Return the string expression for an AST node."""
    for type_, parse in PARSE_NODE_FUNCTIONS:
        if isinstance(node, type_):
            node_str = parse(node) if callable(parse) else getattr(node, parse)
            return node_str if isinstance(node_str, str) else str(node_str)
    return ast.unparse(node)
