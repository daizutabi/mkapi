"""Link module."""
from __future__ import annotations

import ast
import re
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Literal, TypeAlias

import mkapi.ast
import mkapi.markdown
from mkapi.nodes import resolve
from mkapi.objects import Attribute, Class, Function, Module
from mkapi.utils import is_identifier, iter_identifiers, iter_parent_module_names

PREFIX = "__mkapi__."

LINK_PATTERN = re.compile(r"(?<!\])\[(?P<name>[^[\]\s\(\)]+?)\](\[\])?(?![\[\(])")


def get_markdown_link(name: str, ref: str | None) -> str:
    name = name.replace("_", "\\_")
    return f"[{name}][{PREFIX}{ref}]" if ref else name


Replace: TypeAlias = Callable[[str], str | None] | None


def get_markdown_name(fullname: str, replace: Replace = None) -> str:
    """Return markdown links"""
    names = fullname.split(".")
    refs = iter_parent_module_names(fullname)

    if replace:
        refs = [replace(ref) for ref in refs]

    it = zip(names, refs, strict=True)
    return ".".join(get_markdown_link(*names) for names in it)


def get_markdown_str(type_string: str, replace: Replace) -> str:
    """Return markdown links from string-type."""
    it = iter_identifiers(type_string)
    markdowns = (get_markdown_name(name, replace) if is_ else name for name, is_ in it)
    return "".join(markdowns)


def get_markdown_expr(expr: ast.expr, replace: Replace = None) -> str:
    """Set Markdown text with link."""
    if isinstance(expr, ast.Constant):
        value = expr.value

        if isinstance(value, str):
            return get_markdown_str(value, replace)

        return str(value)

    def get_link(name: str) -> str:
        return get_markdown_name(name, replace)

    try:
        return mkapi.ast.unparse(expr, get_link)
    except ValueError:
        return ast.unparse(expr)


def get_markdown_text(text: str, replace: Replace) -> str:
    """Return markdown links from docstring text."""

    def _replace(match: re.Match) -> str:
        name = match.group("name")

        if name.startswith("__mkapi__."):
            from_mkapi = True
            name = name[10:]
        else:
            from_mkapi = False

        if is_identifier(name) and replace and (ref := replace(name)):
            return get_markdown_link(name, ref)

        if from_mkapi:
            return name

        return match.group()

    return mkapi.markdown.sub(LINK_PATTERN, _replace, text)
