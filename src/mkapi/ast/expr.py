"""Parse expr node."""
from __future__ import annotations

import ast
from ast import Attribute, Call, Constant, List, Name, Slice, Starred, Subscript, Tuple
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypeAlias

# Callback: TypeAlias = Callable[[ast.expr], str | ast.expr | None] | None
type Callback = Callable[[ast.expr], str | ast.expr]  # Python 3.12


def _parse_attribute(node: Attribute, callback: Callback) -> str:
    return ".".join([parse_expr(node.value, callback), node.attr])


def _parse_subscript(node: Subscript, callback: Callback) -> str:
    value = parse_expr(node.value, callback)
    if isinstance(node.slice, Slice):
        slice_ = _parse_slice(node.slice, callback)
    elif isinstance(node.slice, Tuple):
        slice_ = _parse_elts(node.slice.elts, callback)
    else:
        slice_ = parse_expr(node.slice, callback)
    return f"{value}[{slice_}]"


def _parse_slice(node: Slice, callback: Callback) -> str:
    lower = parse_expr(node.lower, callback) if node.lower else ""
    upper = parse_expr(node.upper, callback) if node.upper else ""
    step = ":" + parse_expr(node.step, callback) if node.step else ""
    return f"{lower}:{upper}{step}"


def _parse_starred(node: Starred, callback: Callback) -> str:
    return "*" + parse_expr(node.value, callback)


def _parse_call(node: Call, callback: Callback) -> str:
    func = parse_expr(node.func, callback)
    args = ", ".join(parse_expr(arg, callback) for arg in node.args)
    it = [_parse_keyword(keyword, callback) for keyword in node.keywords]
    keywords = (", " + ", ".join(it)) if it else ""
    return f"{func}({args}{keywords})"


def _parse_keyword(node: ast.keyword, callback: Callback) -> str:
    value = parse_expr(node.value, callback)
    return f"**{value}" if node.arg is None else f"{node.arg}={value}"


def _parse_elts(nodes: list[ast.expr], callback: Callback) -> str:
    return ", ".join(parse_expr(node, callback) for node in nodes)


def _parse_list(node: List, callback: Callback) -> str:
    return f"[{_parse_elts(node.elts,callback)}]"


def _parse_tuple(node: Tuple, callback: Callback) -> str:
    elts = _parse_elts(node.elts, callback)
    if len(node.elts) == 1:
        elts = elts + ","
    return f"({elts})"


def _parse_name(node: Name, _: Callback) -> str:
    return node.id


def _parse_constant(node: Constant, _: Callback) -> str:
    if node.value is Ellipsis:
        return "..."
    if isinstance(node.value, str):
        return f"{node.value!r}"
    return str(node.value)


PARSE_EXPR_FUNCTIONS: list[tuple[type, Callable[..., str]]] = [
    (Attribute, _parse_attribute),
    (Subscript, _parse_subscript),
    (Constant, _parse_constant),
    (Starred, _parse_starred),
    (Call, _parse_call),
    (List, _parse_list),
    (Tuple, _parse_tuple),
    (Name, _parse_name),
]


def parse_expr(expr: ast.expr, callback: Callback = None) -> str:
    """Return the string expression for an expr."""
    if callback and isinstance(expr_str := callback(expr), str):
        return expr_str
    for type_, parse in PARSE_EXPR_FUNCTIONS:
        if isinstance(expr, type_):
            return parse(expr, callback)
    return ast.unparse(expr)
