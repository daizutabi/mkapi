"""Provide functions that relate to linking functionality."""
import os
import re
import warnings
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from mkapi.core.object import get_fullname

LINK_PATTERN = re.compile(r"\[(.+?)\]\((.+?)\)")
REPLACE_LINK_PATTERN = re.compile(r"\[(.*?)\]\((.*?)\)|(\S+)_")


def link(name: str, href: str) -> str:
    """Return Markdown link with a mark that indicates this link was created by MkAPI.

    Args:
        name: Link name.
        href: Reference.

    Examples:
        >>> link('abc', 'xyz')
        '[abc](!xyz)'
    """
    return f"[{name}](!{href})"


def get_link(obj: type, *, include_module: bool = False) -> str:
    """Return Markdown link for object, if possible.

    Args:
        obj: Object
        include_module: If True, link text includes module path.

    Examples:
        >>> get_link(int)
        'int'
        >>> get_link(get_fullname)
        '[get_fullname](!mkapi.core.object.get_fullname)'
        >>> get_link(get_fullname, include_module=True)
        '[mkapi.core.object.get_fullname](!mkapi.core.object.get_fullname)'
    """
    if hasattr(obj, "__qualname__"):
        name = obj.__qualname__
    elif hasattr(obj, "__name__"):
        name = obj.__name__
    else:
        msg = f"obj has no name: {obj}"
        warnings.warn(msg, stacklevel=1)
        return str(obj)

    if not hasattr(obj, "__module__") or (module := obj.__module__) == "builtins":
        return name
    fullname = f"{module}.{name}"
    text = fullname if include_module else name
    if obj.__name__.startswith("_"):
        return text
    return link(text, fullname)


def resolve_link(markdown: str, abs_src_path: str, abs_api_paths: list[str]) -> str:
    """Reutrn resolved link.

    Args:
        markdown: Markdown source.
        abs_src_path: Absolute source path of Markdown.
        abs_api_paths: List of API paths.

    Examples:
        >>> abs_src_path = '/src/examples/example.md'
        >>> abs_api_paths = ['/api/a','/api/b', '/api/b.c']
        >>> resolve_link('[abc](!b.c.d)', abs_src_path, abs_api_paths)
        '[abc](../../api/b.c#b.c.d)'
    """

    def replace(match: re.Match) -> str:
        name, href = match.groups()
        if href.startswith("!!"):  # Just for MkAPI documentation.
            href = href[2:]
            return f"[{name}]({href})"
        if href.startswith("!"):
            href = href[1:]
            from_mkapi = True
        else:
            from_mkapi = False

        href = _resolve_href(href, abs_src_path, abs_api_paths)
        if href:
            return f"[{name}]({href})"
        if from_mkapi:
            return name
        return match.group()

    return re.sub(LINK_PATTERN, replace, markdown)


def _resolve_href(name: str, abs_src_path: str, abs_api_paths: list[str]) -> str:
    if not name:
        return ""
    abs_api_path = _match_last(name, abs_api_paths)
    if not abs_api_path:
        return ""
    relpath = os.path.relpath(abs_api_path, Path(abs_src_path).parent)
    relpath = relpath.replace("\\", "/")
    return f"{relpath}#{name}"


def _match_last(name: str, abs_api_paths: list[str]) -> str:
    match = ""
    for abs_api_path in abs_api_paths:
        _, path = os.path.split(abs_api_path)
        if name.startswith(path[:-3]):
            match = abs_api_path
    return match


class _ObjectParser(HTMLParser):
    def feed(self, html: str) -> dict[str, Any]:
        self.context = {"href": [], "heading_id": ""}
        super().feed(html)
        href = self.context["href"]
        if len(href) == 2:  # noqa: PLR2004
            prefix_url, name_url = href
        elif len(href) == 1:
            prefix_url, name_url = "", href[0]
        else:
            prefix_url, name_url = "", ""
        self.context["prefix_url"] = prefix_url
        self.context["name_url"] = name_url
        del self.context["href"]
        return self.context

    def handle_starttag(self, tag: str, attrs: list[str]) -> None:
        context = self.context
        if tag == "p":
            context["level"] = 0
        elif re.match(r"h[1-6]", tag):
            context["level"] = int(tag[1:])
            for attr in attrs:
                if attr[0] == "id":
                    self.context["heading_id"] = attr[1]
        elif tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    href = attr[1]
                    if href.startswith("./"):
                        href = href[2:]
                    self.context["href"].append(href)


parser = _ObjectParser()


def resolve_object(html: str) -> dict[str, Any]:
    """Reutrn an object context dictionary.

    Args:
        html: HTML source.

    Examples:
        >>> resolve_object("<p><a href='a'>p</a><a href='b'>n</a></p>")
        {'heading_id': '', 'level': 0, 'prefix_url': 'a', 'name_url': 'b'}
        >>> resolve_object("<h2 id='i'><a href='a'>p</a><a href='b'>n</a></h2>")
        {'heading_id': 'i', 'level': 2, 'prefix_url': 'a', 'name_url': 'b'}
    """
    parser.reset()
    return parser.feed(html)


def replace_link(obj: object, markdown: str) -> str:
    """Return a replaced link with object's full name.

    Args:
        obj: Object that has a module.
        markdown: Markdown

    Examples:
        >>> from mkapi.core.object import get_object
        >>> obj = get_object('mkapi.core.structure.Object')
        >>> replace_link(obj, '[Signature]()')
        '[Signature](!mkapi.inspect.signature.Signature)'
        >>> replace_link(obj, '[](Signature)')
        '[Signature](!mkapi.inspect.signature.Signature)'
        >>> replace_link(obj, '[text](Signature)')
        '[text](!mkapi.inspect.signature.Signature)'
        >>> replace_link(obj, '[dummy.Dummy]()')
        '[dummy.Dummy]()'
        >>> replace_link(obj, 'Signature_')
        '[Signature](!mkapi.inspect.signature.Signature)'
    """

    def replace(match: re.Match) -> str:
        text, name, rest = match.groups()
        if rest:
            name, text = rest, ""
        elif not name:
            name, text = text, ""
        fullname = get_fullname(obj, name)
        if fullname == "":
            return match.group()
        return link(text or name, fullname)

    return re.sub(REPLACE_LINK_PATTERN, replace, markdown)
