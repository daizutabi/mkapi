"""Page class."""

from __future__ import annotations

import os.path
import re
from dataclasses import dataclass
from enum import Enum
from functools import partial
from pathlib import PurePath
from typing import TYPE_CHECKING

import astdoc.markdown
from astdoc.node import get_module_members
from astdoc.utils import get_module_node

import mkapi.renderer
from mkapi.renderer import TemplateKind

if TYPE_CHECKING:
    from collections.abc import Callable

    from astdoc.parser import Parser


class PageKind(Enum):
    """Enum representing different types of pages."""

    OBJECT = "object"
    SOURCE = "source"
    DOCUMENTATION = "documentation"


URIS: dict[str, dict[str, str]] = {}


@dataclass
class Page:
    """Page class."""

    src_uri: str
    name: str
    markdown: str
    kind: PageKind

    @classmethod
    def create_object(cls, src_uri: str, name: str) -> Page:
        """Create an object page."""
        return cls(src_uri, name, "", PageKind.OBJECT)

    @classmethod
    def create_source(cls, src_uri: str, name: str) -> Page:
        """Create a source page."""
        return cls(src_uri, name, "", PageKind.SOURCE)

    @classmethod
    def create_documentation(cls, src_uri: str, content: str) -> Page:
        """Create a documentation page."""
        return cls(src_uri, "", content, PageKind.DOCUMENTATION)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.src_uri!r})"

    def is_object_page(self) -> bool:
        """Check if the page is an object page."""
        return self.kind is PageKind.OBJECT

    def is_source_page(self) -> bool:
        """Check if the page is a source page."""
        return self.kind is PageKind.SOURCE

    def is_api_page(self) -> bool:
        """Check if the page is an API page."""
        return self.is_object_page() or self.is_source_page()

    def is_documentation_page(self) -> bool:
        """Check if the page is a documentation page."""
        return not self.is_api_page()

    def generate_markdown(self) -> None:
        """Generate markdown for the page."""
        self.markdown, names = generate_module_markdown(self.name)
        namespace = "source" if self.is_source_page() else "object"
        uris = URIS.setdefault(namespace, {})

        for name in names:
            uris[name] = self.src_uri

    def convert_markdown(self, markdown: str) -> str:
        """Convert markdown for the page."""
        if self.is_api_page():
            markdown = self.markdown

        if self.is_source_page():
            namespaces = ("source", "object")
        else:
            namespaces = ("object", "source")

        def predicate(parser: Parser, kind: TemplateKind) -> bool:
            if kind == TemplateKind.HEADING:
                return True

            if kind == TemplateKind.OBJECT and parser.name == self.name:
                return True

            if self.is_source_page():
                return bool(kind == TemplateKind.SOURCE and self.name == parser.name)

            return kind != TemplateKind.SOURCE

        return convert_markdown(markdown, self.src_uri, namespaces, predicate)

    def convert_html(self, html: str) -> str:
        """Return converted html."""
        namespace = "object" if self.is_source_page() else "source"
        return convert_html(html, self.src_uri, namespace)


def generate_module_markdown(module: str) -> tuple[str, list[str]]:
    """Create module page."""
    if not get_module_node(module):
        return f"!!! failure\n\n    module {module!r} not found.\n", []

    markdowns = [f"# ::: {module}"]
    names = [module]

    for name, _ in get_module_members(module, private=False, special=False):
        level = name.count(".") + 2
        markdown = f"{'#' * level} ::: {name} {module}"
        markdowns.append(markdown)
        names.append(f"{module}.{name}")

    return "\n".join(markdowns), names


OBJECT_PATTERN = re.compile(r"^(#*) *?::: (.+?)$", re.MULTILINE)
LINK_PATTERN = re.compile(r"(?<!`)\[([^[\]\s]+?)\]\[([^[\]\s]*?)\]")


def convert_markdown(
    markdown: str,
    src_uri: str,
    namespaces: tuple[str, str],
    predicate: Callable[[Parser, TemplateKind], bool] | None = None,
) -> str:
    """Return converted markdown."""
    render = partial(_render, namespace=namespaces[1], predicate=predicate)
    markdown = astdoc.markdown.sub(OBJECT_PATTERN, render, markdown)

    link = partial(_link, src_uri=src_uri, namespace=namespaces[0])
    return astdoc.markdown.sub(LINK_PATTERN, link, markdown)


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


OBJECT_LINK_PATTERN = re.compile(r"^__mkapi__\.__(.+)__\.(.+)$")
ANCHOR_PLACEHOLDERS = {
    "object": "mkapi_object_mkapi",
    "source": "mkapi_source_mkapi",
    "definition": "mkapi_definition_mkapi",
}
ANCHOR_TITLES = {
    "object": "Go to docs",
    "source": "Go to source",
    "definition": "Go to definition",
}


def _link(match: re.Match, src_uri: str, namespace: str) -> str:
    name, fullname = match.groups()
    if not fullname:
        fullname = name
        if name.startswith("`") and name.endswith("`"):
            fullname = name[1:-1]

    asname = title = ""

    if m := OBJECT_LINK_PATTERN.match(fullname):
        is_object_link = True
        namespace, fullname = m.groups()

        if namespace == "definition" and "object" in URIS:
            name = ANCHOR_PLACEHOLDERS[namespace]
            title = ANCHOR_TITLES[namespace]
            namespace = "object"
        elif namespace in ANCHOR_PLACEHOLDERS and namespace in URIS:
            name = ANCHOR_PLACEHOLDERS[namespace]
        else:
            return ""

    else:
        is_object_link = False
        asname = match.group()

    if fullname.startswith("__mkapi__."):
        from_mkapi = True
        fullname = fullname[10:]
    else:
        from_mkapi = False

    if uri := URIS[namespace].get(fullname):
        uri = os.path.relpath(uri, PurePath(src_uri).parent)
        uri = uri.replace("\\", "/")  # Normalize for Windows
        if not title:
            title = ANCHOR_TITLES[namespace] if is_object_link else fullname
        return f'[{name}]({uri}#{fullname} "{title}")'

    if from_mkapi and name != ANCHOR_PLACEHOLDERS["definition"]:
        return f'<span class="mkapi-tooltip" title="{fullname}">{name}</span>'

    return asname


SOURCE_LINK_PATTERN = re.compile(r"(<span[^<]+?)## __mkapi__\.(\S+?)(</span>)")
HEADING_PATTERN = re.compile(r"<h(\d).+?mkapi-heading.+?>(.+?)</h\d>\n?")

ANCHOR_TEXTS = {
    "object": "docs",
    "source": "source",
    "definition": '<i class="fa-solid fa-square-arrow-up-right"></i>',
}


def convert_html(html: str, src_uri: str, namespace: str) -> str:
    """Convert HTML for source pages."""
    for name, anchor in ANCHOR_TEXTS.items():
        html = html.replace(ANCHOR_PLACEHOLDERS[name], anchor)

    link = partial(_link_source, src_uri=src_uri, namespace=namespace)
    html = SOURCE_LINK_PATTERN.sub(link, html)

    return HEADING_PATTERN.sub(_heading, html)


def _link_source(match: re.Match, src_uri: str, namespace: str) -> str:
    anchor = ANCHOR_TEXTS[namespace]
    open_tag, name, close_tag = match.groups()

    if uri := URIS[namespace].get(name):
        uri = os.path.relpath(uri, src_uri)
        uri = uri[:-3]  # Remove `.md`
        uri = uri.replace("/README", "")  # Remove `/README`

        href = f"{uri}/#{name}"
        title = ANCHOR_TITLES[namespace]
        link = f'<a href="{href}" title="{title}">{anchor}</a>'
        # https://github.com/daizutabi/mkapi/issues/123: <span> -> <div>
        link = f'<div class="mkapi-source-link" id="{name}">{link}</div>'
    else:
        link = ""

    if open_tag.endswith(">"):
        return link

    return f"{open_tag}{close_tag}{link}"


def _heading(match: re.Match) -> str:
    if match.group(1) == "1":
        name = match.group(2)
        return f'<h1 style="display: none;">{name}</h1>'

    return ""
