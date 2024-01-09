"""Inspect module."""
from __future__ import annotations

import ast
import inspect
from ast import FunctionDef
from inspect import Parameter, Signature
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import _IntrospectableCallable


def _stringize_signature(signature: Signature) -> str:
    ps = []
    for p in signature.parameters.values():
        ps.append(p.replace(default=inspect.Parameter.empty))  # noqa: PERF401
    sig_str = str(signature.replace(parameters=ps)).replace("'", "")
    print(sig_str)
    return sig_str


def get_node_from_callable(obj: _IntrospectableCallable) -> FunctionDef:
    signature = inspect.signature(obj)
    sig_str = _stringize_signature(signature)
    source = f"def f{sig_str}:\n pass"
    node = ast.parse(source).body[0]
    if not isinstance(node, FunctionDef):
        raise NotImplementedError
    return node
