import os
import re
from typing import List

from mkapi.core.base import Base, Node

LINK_PATTERN = re.compile(r"\[(.+?)\]\((.+?)\)")


def resolve_link(base: Base, abs_src_path: str, api_roots: List[str]):
    if isinstance(base, Node):
        resolve_node_link(base, abs_src_path, api_roots)
    resolve_type_link(base, abs_src_path, api_roots)


def resolve_node_link(node: Node, abs_src_path: str, api_roots: List[str]):
    node.prefix_url = resolve_href(node.prefix, abs_src_path, api_roots)
    if node.prefix_url:
        node.name_url = ".".join([node.prefix_url, node.name])


def resolve_type_link(base: Base, abs_src_path: str, api_roots: List[str]):
    def replace(match):
        name = match.group(1)
        href = resolve_href(match.group(2), abs_src_path, api_roots)
        if href:
            title = href.split('#')[1]
            return f'<a href="{href}" title="{title}">{match.group(1)}</a>'
        else:
            return name

    base.type = re.sub(LINK_PATTERN, replace, base.type)


def resolve_markdown_link(
    markdown: str, abs_src_path: str, api_roots: List[str]
) -> str:
    def replace(match):
        name = match.group(1)
        if match.group(2).startswith("!"):  # Just for MkApi documentation.
            href = match.group(2)[1:]
            return f"[{name}]({href})"
        href = resolve_href(match.group(2), abs_src_path, api_roots, drop_ext=False)
        if href:
            return f"[{name}]({href})"
        else:
            return match.group()

    return re.sub(LINK_PATTERN, replace, markdown)


def resolve_href(
    name: str, abs_src_path: str, api_roots: List[str], drop_ext: bool = True
) -> str:
    if not name:
        return ""
    for root in api_roots:
        dirname, path = os.path.split(root)
        if name.startswith(path[:-3]):
            if drop_ext:
                relpath = os.path.relpath(root, abs_src_path)
            else:
                relpath = os.path.relpath(root, os.path.dirname(abs_src_path))
            if drop_ext:
                relpath = relpath[:-3]
            relpath = relpath.replace("\\", "/")
            return "#".join([relpath, name])
    return ""
