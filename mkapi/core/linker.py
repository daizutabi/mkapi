import os
import re
from typing import List, Union

from mkapi.core.base import Base
from mkapi.core.node import Node
from mkapi.core.regex import LINK_PATTERN


def resolve_link(node: Node, abs_src_path: str, api_roots: List[str]):
    resolve_node_link(node, abs_src_path, api_roots)
    for base in node:
        resolve_type_link(base, abs_src_path, api_roots)


def resolve_node_link(node: Node, abs_src_path: str, api_roots: List[str]):
    node.prefix_url = resolve_href(node.prefix, abs_src_path, api_roots, is_html=True)
    if node.prefix_url:
        node.name_url = ".".join([node.prefix_url, node.name])
    resolve_type_link(node, abs_src_path, api_roots)
    for member in node.members:
        resolve_node_link(member, abs_src_path, api_roots)


def resolve_type_link(base: Union[Base, Node], abs_src_path: str, api_roots: List[str]):
    def replace(match):
        name = match.group(1)
        href = resolve_href(match.group(2), abs_src_path, api_roots, is_html=True)
        if href:
            title = href.split("#")[1]
            return f'<a href="{href}" title="{title}">{match.group(1)}</a>'
        else:
            return name

    base.type_html = re.sub(LINK_PATTERN, replace, base.type)


def resolve_markdown_link(
    markdown: str, abs_src_path: str, api_roots: List[str]
) -> str:
    def replace(match):
        name = match.group(1)
        if match.group(2).startswith("!"):  # Just for MkApi documentation.
            href = match.group(2)[1:]
            return f"[{name}]({href})"
        href = resolve_href(match.group(2), abs_src_path, api_roots, is_html=False)
        if href:
            return f"[{name}]({href})"
        else:
            return match.group()

    return re.sub(LINK_PATTERN, replace, markdown)


def resolve_href(
    name: str, abs_src_path: str, api_roots: List[str], is_html: bool
) -> str:
    if not name:
        return ""
    for root in api_roots:
        dirname, path = os.path.split(root)
        if name.startswith(path[:-3]):
            if is_html:
                relpath = os.path.relpath(root, abs_src_path)
            else:
                relpath = os.path.relpath(root, os.path.dirname(abs_src_path))
            if is_html:
                relpath = relpath[:-3]
            relpath = relpath.replace("\\", "/")
            return "#".join([relpath, name])
    return ""
