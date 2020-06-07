import os
import re
from html.parser import HTMLParser
from typing import Any, Dict, List

from mkapi.core.regex import LINK_PATTERN


def link(name: str, href: str) -> str:
    return f"[{name}](!{href})"


def resolve_link(markdown: str, abs_src_path: str, abs_api_paths: List[str]) -> str:
    def replace(match):
        name, href = match.groups()
        if href.startswith("!!"):  # Just for MkApi documentation.
            href = href[2:]
            return f"[{name}]({href})"
        if href.startswith("!"):
            href = href[1:]
            from_mkapi = True
        else:
            from_mkapi = False

        href = resolve_href(href, abs_src_path, abs_api_paths)
        if href:
            return f"[{name}]({href})"
        elif from_mkapi:
            return name
        else:
            return match.group()

    return re.sub(LINK_PATTERN, replace, markdown)


def resolve_href(name: str, abs_src_path: str, abs_api_paths: List[str]) -> str:
    if not name:
        return ""
    abs_api_path = match_last(name, abs_api_paths)
    if not abs_api_path:
        return ""
    relpath = os.path.relpath(abs_api_path, os.path.dirname(abs_src_path))
    relpath = relpath.replace("\\", "/")
    return "#".join([relpath, name])


def match_last(name: str, abs_api_paths: List[str]) -> str:
    match = ""
    for abs_api_path in abs_api_paths:
        dirname, path = os.path.split(abs_api_path)
        if name.startswith(path[:-3]):
            match = abs_api_path
    return match


class ObjectParser(HTMLParser):
    def feed(self, html):
        self.context = {"href": [], "heading_id": ""}
        super().feed(html)
        href = self.context["href"]
        if len(href) == 2:
            prefix_url, name_url = href
        elif len(href) == 1:
            prefix_url, name_url = "", href[0]
        else:
            prefix_url, name_url = "", ""
        self.context["prefix_url"] = prefix_url
        self.context["name_url"] = name_url
        del self.context["href"]
        return self.context

    def handle_starttag(self, tag, attrs):
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


parser = ObjectParser()


def resolve_object(html: str) -> Dict[str, Any]:
    parser.reset()
    return parser.feed(html)
