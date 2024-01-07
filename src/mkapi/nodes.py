"""Node class represents Markdown and HTML structure."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mkapi.objects import (
    Attribute,
    Class,
    Function,
    Module,
    Object,
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
    object: Module | Class | Function | Attribute | Parameter | Raise | Return  # noqa: A003
    kind: str
    parent: Node | None
    members: list[Node] | None

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.name!r}, members={len(self)})"

    def __len__(self) -> int:
        return len(self.members or [])

    def __contains__(self, name: str) -> bool:
        if self.members:
            return any(member.object.name == name for member in self.members)
        return False

    def get(self, name: str) -> Node | None:  # noqa: D102
        return get_by_name(self.members, name) if self.members else None

    def get_kind(self) -> str:
        """Returns kind of self."""
        raise NotImplementedError

    def get_markdown(self) -> str:
        """Returns a Markdown source for docstring of self."""
        return f"<{self.name}@{id(self)}>"

    def walk(self) -> Iterator[Node]:
        """Yields all members."""
        yield self
        if self.members:
            for member in self.members:
                yield from member.walk()


def get_node(name: str) -> Node:
    """Return a [Node] instance from the object name."""
    obj = get_object(name)
    if not obj or not isinstance(obj, Module | Class | Function):
        raise NotImplementedError
    return _get_node(obj)


def _get_node(obj: Module | Class | Function, parent: Node | None = None) -> Node:
    """Return a [Node] instance of [Module], [Class], and [Function]."""
    node = Node(obj.name, obj, _get_kind(obj), parent, [])
    if isinstance(obj, Module):
        node.members = list(_iter_members_module(node, obj))
    elif isinstance(obj, Class):
        node.members = list(_iter_members_class(node, obj))
    elif isinstance(obj, Function):
        node.members = list(_iter_members_function(node, obj))
    else:
        raise NotImplementedError
    return node


def _iter_members_module(node: Node, obj: Module | Class) -> Iterator[Node]:
    yield from _iter_attributes(node, obj)
    yield from _iter_classes(node, obj)
    yield from _iter_functions(node, obj)


def _iter_members_class(node: Node, obj: Class) -> Iterator[Node]:
    yield from _iter_members_module(node, obj)
    yield from _iter_parameters(node, obj)
    yield from _iter_raises(node, obj)
    # bases


def _iter_members_function(node: Node, obj: Function) -> Iterator[Node]:
    yield from _iter_parameters(node, obj)
    yield from _iter_raises(node, obj)
    yield from _iter_returns(node, obj)


def _iter_attributes(node: Node, obj: Module | Class) -> Iterator[Node]:
    for attr in obj.attributes:
        yield Node(attr.name, attr, _get_kind(attr), node, None)


def _iter_parameters(node: Node, obj: Class | Function) -> Iterator[Node]:
    for arg in obj.parameters:
        yield Node(arg.name, arg, _get_kind(arg), node, None)


def _iter_raises(node: Node, obj: Class | Function) -> Iterator[Node]:
    for raises in obj.raises:
        yield Node(raises.name, raises, _get_kind(raises), node, None)


def _iter_returns(node: Node, obj: Function) -> Iterator[Node]:
    rt = obj.returns
    yield Node(rt.name, rt, _get_kind(rt), node, None)


def _iter_classes(node: Node, obj: Module | Class) -> Iterator[Node]:
    for cls in obj.classes:
        yield _get_node(cls, node)


def _iter_functions(node: Node, obj: Module | Class) -> Iterator[Node]:
    for func in obj.functions:
        yield _get_node(func, node)


def _get_kind(obj: Object) -> str:
    return obj.__class__.__name__.lower()
