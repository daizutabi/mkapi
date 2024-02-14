"""Link module."""
from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypeAlias

import mkapi.markdown
from mkapi.utils import is_identifier, iter_identifiers, iter_parent_module_names

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


# def get_fullname_from_object(
#     obj: Module | Class | Function | Attribute,
#     name: str,
# ) -> str | None:
#     """Return fullname from object."""
#     for child in iter_objects(obj, maxdepth=1):
#         if child.name.str == name:
#             return child.fullname.str
#     if isinstance(obj, Module):
#         return get_fullname(obj.name.str, name)
#     if obj.parent and isinstance(obj.parent, Class | Function):
#         return get_fullname_from_object(obj.parent, name)
#     if "." not in name:
#         return get_fullname_from_object(obj.module, name)
#     parent, attr = name.rsplit(".", maxsplit=1)
#     if parent == obj.name.str:
#         return get_fullname_from_object(obj, attr)
#     return resolve_with_attribute(name)
