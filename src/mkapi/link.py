"""Link module."""
from __future__ import annotations

from mkapi.globals import get_fullname
from mkapi.utils import cache, iter_identifiers, iter_parent_module_names


def get_markdown_from_name(fullname: str) -> str:
    names = []
    parents = iter_parent_module_names(fullname)
    asnames = fullname.split(".")
    for name, asname in zip(parents, asnames, strict=True):
        asname_ = asname.replace("_", "\\_")
        names.append(f"[{asname_}][__mkapi__.{name}]")
    return ".".join(names)


def _get_markdown(module: str, name: str, asname: str) -> str:
    fullname = get_fullname(module, name)
    asname = asname.replace("_", "\\_")
    return f"[{asname}][__mkapi__.{fullname}]" if fullname else asname


@cache
def get_markdown_from_type(module: str, name: str) -> str:
    """Return markdown links from type."""
    names = []
    parents = iter_parent_module_names(name)
    asnames = name.split(".")
    for name, asname in zip(parents, asnames, strict=True):
        names.append(_get_markdown(module, name, asname))
    return ".".join(names)


def get_markdown_from_type_string(module: str, source: str) -> str:
    """Return markdown links from string-type."""
    strs = []
    for name, isidentifier in iter_identifiers(source):
        if isidentifier:
            strs.append(get_markdown_from_type(module, name))
        else:
            strs.append(name)
    return "".join(strs)
