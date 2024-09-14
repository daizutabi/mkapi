"""Page class that works with other converter."""

from __future__ import annotations

import os.path
import re
from dataclasses import dataclass
from enum import Enum
from functools import partial
from pathlib import PurePath
from typing import TYPE_CHECKING

import mkapi.markdown
import mkapi.renderer
from mkapi.node import iter_module_members
from mkapi.renderer import TemplateKind
from mkapi.utils import get_module_node

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkapi.parser import Parser


class PageKind(Enum):
    OBJECT = "object"
    SOURCE = "source"
    DOCUMENTATION = "documentation"


URIS: dict[str, dict[str, str]] = {}


@dataclass
class Page:
    """Page class"""

    src_uri: str
    name: str
    markdown: str
    kind: PageKind

    @staticmethod
    def create_object(src_uri: str, name: str) -> Page:
        return Page(src_uri, name, "", PageKind.OBJECT)

    @staticmethod
    def create_source(src_uri: str, name: str) -> Page:
        return Page(src_uri, name, "", PageKind.SOURCE)

    @staticmethod
    def create_documentation(src_uri: str, content: str) -> Page:
        return Page(src_uri, "", content, PageKind.DOCUMENTATION)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.src_uri!r})"

    def is_object_page(self) -> bool:
        return self.kind is PageKind.OBJECT

    def is_source_page(self) -> bool:
        return self.kind is PageKind.SOURCE

    def is_api_page(self) -> bool:
        return self.is_object_page() or self.is_source_page()

    def is_documentation_page(self) -> bool:
        return not self.is_api_page()

    def generate_markdown(self) -> None:
        self.markdown, names = generate_module_markdown(self.name)
        namespace = "source" if self.is_source_page() else "object"
        uris = URIS.setdefault(namespace, {})

        for name in names:
            uris[name] = self.src_uri

    def convert_markdown(self, markdown: str, anchors: dict[str, str]) -> str:
        if self.is_api_page():
            markdown = self.markdown

        if self.is_source_page():
            namespaces = ("source", "object")
        else:
            namespaces = ("object", "source")

        def predicate(parser: Parser, kind: TemplateKind) -> bool:
            if kind == TemplateKind.HEADING:
                return True

            if self.is_source_page():
                if self.name == parser.name and kind == TemplateKind.SOURCE:
                    return True

                return False

            # if kind == TemplateKind.OBJECT and parser.name == self.name:
            #     return False

            return kind != TemplateKind.SOURCE

        return convert_markdown(markdown, self.src_uri, namespaces, anchors, predicate)

    def convert_html(self, html: str, anchors: dict[str, str]) -> str:
        """Return converted html."""
        namespace = "object" if self.is_source_page() else "source"
        anchor = anchors[namespace]

        return convert_html(html, self.src_uri, namespace, anchor)


def generate_module_markdown(module: str) -> tuple[str, list[str]]:
    """Create module page."""
    if not get_module_node(module):
        return f"!!! failure\n\n    module {module!r} not found.\n", []

    markdowns = [f"# ::: {module}"]
    names = [module]

    for name, _ in iter_module_members(module, private=False, special=False):
        level = name.count(".") + 2
        markdown = f"{'#' * level} ::: {name} {module}"
        markdowns.append(markdown)
        names.append(f"{module}.{name}")

    return "\n".join(markdowns), names


OBJECT_PATTERN = re.compile(r"^(#*) *?::: (.+?)$", re.M)
LINK_PATTERN = re.compile(r"(?<!`)\[([^[\]\s]+?)\]\[([^[\]\s]*?)\]")


def convert_markdown(
    markdown: str,
    src_uri: str,
    namespaces: tuple[str, str],
    anchors: dict[str, str],
    predicate: Callable[[Parser, TemplateKind], bool] | None = None,
) -> str:
    """Return converted markdown."""
    render = partial(_render, namespace=namespaces[1], predicate=predicate)
    markdown = mkapi.markdown.sub(OBJECT_PATTERN, render, markdown)

    link = partial(_link, src_uri=src_uri, namespace=namespaces[0], anchors=anchors)
    return mkapi.markdown.sub(LINK_PATTERN, link, markdown)


def _render(
    match: re.Match,
    namespace: str,
    predicate: Callable[[Parser, TemplateKind], bool] | None = None,
) -> str:
    heading, name = match.groups()

    if " " in name:
        name, module = name.split(" ", 1)
    else:
        module = None

    level = len(heading)
    return mkapi.renderer.render(name, module, level, namespace, predicate)


# Link for [source] or [docs]
OBJECT_LINK_PATTERN = re.compile(r"^__mkapi__\.__(.+)__\.(.+)$")


def _link(
    match: re.Match, src_uri: str, namespace: str, anchors: dict[str, str]
) -> str:
    name, fullname = match.groups()
    if not fullname:
        fullname = name
        if name.startswith("`") and name.endswith("`"):
            fullname = name[1:-1]

    asname = ""

    if m := OBJECT_LINK_PATTERN.match(fullname):
        namespace, fullname = m.groups()

        if namespace in anchors and namespace in URIS:
            name = f"[{anchors[namespace]}]"
        else:
            return ""

    else:
        asname = match.group()

    if fullname.startswith("__mkapi__."):
        from_mkapi = True
        fullname = fullname[10:]
    else:
        from_mkapi = False

    if uri := URIS[namespace].get(fullname):
        uri = os.path.relpath(uri, PurePath(src_uri).parent)
        uri = uri.replace("\\", "/")  # Normalize for Windows
        return f'[{name}]({uri}#{fullname} "{fullname}")'

    if from_mkapi:
        return f'<span class="mkapi-tooltip" title="{fullname}">{name}</span>'

    return asname


SOURCE_LINK_PATTERN = re.compile(r"(<span[^<]+?)## __mkapi__\.(\S+?)(</span>)")
HEADING_PATTERN = re.compile(r"<h(\d).+?mkapi-heading.+?</h\d>\n?")


def convert_html(html: str, src_uri: str, namespace: str, anchor: str) -> str:
    """Convert HTML for source pages."""

    link = partial(_link_source, src_uri=src_uri, namespace=namespace, anchor=anchor)
    html = SOURCE_LINK_PATTERN.sub(link, html)

    return HEADING_PATTERN.sub(_heading, html)


def _link_source(match: re.Match, src_uri: str, namespace: str, anchor: str) -> str:
    open_tag, name, close_tag = match.groups()

    if uri := URIS[namespace].get(name):
        uri = os.path.relpath(uri, src_uri)
        uri = uri[:-3]  # Remove `.md`
        uri = uri.replace("/README", "")  # Remove `/README`

        href = f"{uri}/#{name}"
        link = f'<a href="{href}">[{anchor}]</a>'
        # https://github.com/daizutabi/mkapi/issues/123: <span> -> <div>
        link = f'<div class="mkapi-source-link" id="{name}">{link}</div>'
    else:
        link = ""

    if open_tag.endswith(">"):
        return link

    return f"{open_tag}{close_tag}{link}"


def _heading(match: re.Match) -> str:
    # if match.group(1) == "1":
    #     return match.group()

    return ""
