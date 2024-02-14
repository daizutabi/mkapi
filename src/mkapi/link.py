"""Link module."""
from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypeAlias

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

    def replace(match: re.Match) -> str:
        name = match.group("name")
        if name.startswith("__mkapi__."):
            from_mkapi = True
            name = name[10:]
        else:
            from_mkapi = False
        if is_identifier(name) and (fullname := get_fullname_from_object(obj, name)):
            name_ = name.replace("_", "\\_")
            return f"[{name_}][__mkapi__.{fullname}]"
        if from_mkapi:
            return name
        return match.group()

    return re.sub(LINK_PATTERN, replace, text)
