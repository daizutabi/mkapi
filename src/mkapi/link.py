"""Link module."""
from __future__ import annotations

import ast
import itertools
import re
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Literal, TypeAlias

import mkapi.ast
import mkapi.markdown
from mkapi.inspect import get_fullname, resolve_with_attribute
from mkapi.items import Default, Item, Name, Section, Text, Type
from mkapi.objects import Alias, Attribute, Class, Function, Module, iter_objects
from mkapi.utils import is_identifier, iter_identifiers, iter_parent_module_names

if TYPE_CHECKING:
    from mkapi.docstrings import Docstring

PREFIX = "__mkapi__."


def get_markdown_link(name: str, ref: str | None) -> str:
    name = name.replace("_", "\\_")
    return f"[{name}][{PREFIX}{ref}]" if ref else name


Replace: TypeAlias = Callable[[str], str | None] | None


def get_markdown(fullname: str, replace: Replace = None) -> str:
    """Return markdown links"""
    names = fullname.split(".")
    refs = iter_parent_module_names(fullname)
    if replace:
        refs = [replace(ref) for ref in refs]
    it = zip(names, refs, strict=True)
    return ".".join(get_markdown_link(*names) for names in it)


def get_markdown_from_type_string(type_string: str, replace: Replace) -> str:
    """Return markdown links from string-type."""
    it = iter_identifiers(type_string)
    markdowns = (get_markdown(name, replace) if is_ else name for name, is_ in it)
    return "".join(markdowns)


LINK_PATTERN = re.compile(r"(?<!\])\[(?P<name>[^[\]\s\(\)]+?)\](\[\])?(?![\[\(])")


def get_markdown_from_docstring_text(text: str, replace: Replace) -> str:
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


def set_markdown_name(name: Name, replace: Replace = None) -> None:
    """Set Markdown name with link."""
    if name.str:
        name.markdown = get_markdown(name.str, replace)


def set_markdown_type(type_: Type, replace: Replace = None) -> None:
    """Set Markdown text with link."""
    if not (expr := type_.expr):
        return

    if isinstance(expr, ast.Constant):
        value = expr.value
        if isinstance(value, str):
            type_.markdown = get_markdown_from_type_string(value, replace)
        else:
            type_.markdown = str(value)
        return

    def get_link(name: str) -> str:
        return get_markdown(name, replace)

    try:
        type_.markdown = mkapi.ast.unparse(expr, get_link)
    except ValueError:
        type_.markdown = ast.unparse(expr)


def set_markdown_default(default: Default, replace: Replace = None) -> None:  # noqa: ARG001
    """Set Markdown text with link."""
    if default.expr:
        default.markdown = ast.unparse(default.expr)


def set_markdown_text(text: Text, replace: Replace = None) -> None:
    if not text.str:
        return

    text.markdown = get_markdown_from_docstring_text(text.str, replace)


def set_markdown(
    obj: Module | Class | Function | Attribute | Alias,
    doc: Docstring | Section | Item | None | Literal[False] = None,
) -> None:
    # module list for alias
    module = obj if isinstance(obj, Module) else obj.module

    _replace_from_module = partial(get_fullname, module=module.name.str)

    _replace_from_object = partial(replace_from_object, obj=obj)

    match doc:
        case None if not isinstance(obj, Alias):
            it = itertools.chain(obj, obj.doc)
        case None | False:
            it = obj
        case _:
            it = doc

    for elem in it:
        if elem.markdown:
            continue

        if isinstance(elem, Name):
            set_markdown_name(elem, _replace_from_object)  # replace = None ?

        if isinstance(elem, Default):
            set_markdown_default(elem, _replace_from_module)

        elif isinstance(elem, Type):
            set_markdown_type(elem, _replace_from_module)

        elif isinstance(elem, Text):
            set_markdown_text(elem, _replace_from_object)


def replace_from_object(
    name: str,
    obj: Module | Class | Function | Attribute | Alias,
) -> str | None:
    """Return fullname from object."""
    for child in iter_objects(obj, maxdepth=1):
        if child.name.str == name:
            return child.fullname.str

    if isinstance(obj, Module):
        return get_fullname(name, obj.name.str)

    if obj.parent:
        return replace_from_object(name, obj.parent)

    if "." not in name:
        return replace_from_object(name, obj.module)

    parent, attr = name.rsplit(".", maxsplit=1)
    if obj.name.str == parent:
        return replace_from_object(attr, obj)

    return resolve_with_attribute(name)
