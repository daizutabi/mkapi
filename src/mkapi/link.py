"""Link module."""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

from mkapi.utils import iter_identifiers, iter_parent_module_names

PREFIX = "__mkapi__."


def get_name_link(name: str, ref: str | None) -> str:
    name_ = name.replace("_", "\\_")
    return f"[{name_}][{PREFIX}{ref}]" if ref else name


Replace: TypeAlias = Callable[[str], str | None] | None


def get_markdown(fullname: str, replace: Replace = None) -> str:
    """Return markdown links"""
    names = fullname.split(".")
    refs = iter_parent_module_names(fullname)
    if replace:
        refs = [replace(ref) for ref in refs]
    it = zip(names, refs, strict=True)
    return ".".join(get_name_link(*names) for names in it)


def get_markdown_from_type_string(source: str, replace: Replace) -> str:
    """Return markdown links from string-type."""
    it = iter_identifiers(source)
    markdowns = (get_markdown(name, replace) if is_ else name for name, is_ in it)
    return "".join(markdowns)
