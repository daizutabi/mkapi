import inspect
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterator, List, Union

import mkapi.core.preprocess
from mkapi.core.base import Base, Type
from mkapi.core.object import get_object
from mkapi.core.renderer import renderer
from mkapi.core.signature import Signature, get_signature
from mkapi.core.tree import Tree


@dataclass
class Node(Tree):
    """Node class represents an object.

    Attributes:
        obj: Object.
        prefix: Prefix.
        id: ID for CSS.
        kind: Kind such as `function`, `class`, `method`, etc.
        signature: Signature instance.
        docstring: Docstring instance.
        members: Member objects. For example, methods of class.
        html: HTML after rendering.
    """

    members: List["Node"] = field(init=False)
    signature: Signature = field(init=False)
    type: Type = Type()

    def __post_init__(self):
        super().__post_init__()
        self.signature = get_signature(self.obj)

        members = self.members
        if self.kind in ["class", "dataclass"] and not self.docstring:
            for member in members:
                if member.name == "__init__" and member.docstring:
                    markdown = member.docstring.sections[0].markdown
                    if not markdown.startswith("Initialize self"):
                        self.docstring = member.docstring
        self.members = [member for member in members if member.name != "__init__"]
        if self.docstring and self.docstring.type:
            self.type = self.docstring.type

    def __iter__(self) -> Iterator[Union[Base, "Node"]]:
        yield self
        yield from self.docstring
        for member in self.members:
            yield from member

    def get_kind(self) -> str:
        return get_kind(self.obj)

    def get_members(self) -> List["Node"]:  # type:ignore
        return get_members(self.obj)

    def get_markdown(self, level: int = 0) -> str:
        """Returns a Markdown source for docstring of this object."""
        markdowns = []
        for base in self:
            if isinstance(base, Node):
                markdown = base.markdown
                if level:
                    markdown = "#" * level + " " + markdown
            else:
                markdown = mkapi.core.preprocess.convert(base.markdown)
            markdowns.append(markdown)
        return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)

    def set_html(self, html: str):
        """Sets HTML to `Base` instances recursively."""
        for base, html in zip(self, html.split("<!-- mkapi:sep -->")):
            if isinstance(base, Node):
                self.html = html  # FIXME
            else:
                base.set_html(html.strip())

    def render(self) -> str:
        self.html = renderer.render(self)
        return self.html


def get_kind(obj) -> str:
    if isinstance(obj, property):
        if obj.fset:
            return "readwrite_property"
        else:
            return "readonly_property"
    if hasattr(obj, "__dataclass_fields__"):
        return "dataclass"
    if inspect.isclass(obj):
        return "class"
    if inspect.isgeneratorfunction(obj):
        return "generator"
    if inspect.isfunction(obj):
        try:
            parameters = inspect.signature(obj).parameters
        except (ValueError, TypeError):
            return ""
        if parameters:
            arg = list(parameters)[0]
            if arg == "self":
                return "method"
        return "function"
    return ""


def get_members(obj) -> List[Node]:
    if isinstance(obj, property):
        return []

    members = []
    for name, obj in inspect.getmembers(obj):
        if name.startswith("_") and name != "__init__":
            continue
        if not get_kind(obj):
            continue
        member = Node(obj)
        if member.docstring:
            members.append(member)
    return sorted(members, key=lambda x: x.lineno)


@lru_cache(maxsize=1000)
def get_node(name) -> Node:
    if isinstance(name, str):
        obj = get_object(name)
    else:
        obj = name

    return Node(obj)
