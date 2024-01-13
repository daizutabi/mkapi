"""Node class represents Markdown and HTML structure."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from mkapi.objects import (
    Attribute,
    Class,
    Function,
    Module,
    Parameter,
    Raise,
    Return,
    get_object,
)
from mkapi.utils import get_by_name

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class Node:
    """Node class."""

    name: str
    object: Module | Class | Function | Attribute  # noqa: A003
    members: list[Node] = field(default_factory=list, init=False)
    parent: Node | None = None
    html: str = field(init=False)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r}, members={len(self)})"

    def __len__(self) -> int:
        return len(self.members)

    def __contains__(self, name: str) -> bool:
        if self.members:
            return any(member.object.name == name for member in self.members)
        return False

    def get(self, name: str) -> Node | None:  # noqa: D102
        return get_by_name(self.members, name) if self.members else None

    def get_kind(self) -> str:
        """Returns kind of self."""
        raise NotImplementedError

    def walk(self) -> Iterator[Node]:
        """Yields all members."""
        yield self
        for member in self.members:
            yield from member.walk()

    def get_markdown(self, level: int, filters: list[str]) -> str:
        """Returns a Markdown source for docstring of self."""
        markdowns = []
        for node in self.walk():
            markdowns.append(f"{node.object.id}\n\n")  # noqa: PERF401
        return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)

    def convert_html(self, html: str, level: int, filters: list[str]) -> str:
        htmls = html.split("<!-- mkapi:sep -->")
        for node, html in zip(self.walk(), htmls, strict=False):
            node.html = html.strip()
        return "a"


def get_node(name: str) -> Node:
    """Return a [Node] instance from the object name."""
    obj = get_object(name)
    if not isinstance(obj, Module | Class | Function | Attribute):
        raise NotImplementedError
    return _get_node(obj, None)


def _get_node(obj: Module | Class | Function | Attribute, parent: Node | None) -> Node:
    node = Node(obj.name, obj, parent)
    if isinstance(obj, Module | Class):
        node.members = list(_iter_members(node, obj))
    return node


def _iter_members(node: Node, obj: Module | Class) -> Iterator[Node]:
    for member in obj.attributes + obj.classes + obj.functions:
        yield _get_node(member, node)
