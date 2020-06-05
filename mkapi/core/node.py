import inspect
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterator, List

import mkapi.core.preprocess
from mkapi.core.base import Base
from mkapi.core.docstring import Docstring, get_docstring
from mkapi.core.object import (get_object, get_sourcefile_and_lineno,
                               split_prefix_and_name)
from mkapi.core.renderer import renderer
from mkapi.core.signature import Signature, get_signature


@dataclass
class Node(Base):
    """Node class represents an object.

    Attributes:
        obj: Object.
        prefix: Prefix.
        kind: Kind such as `function`, `class`, `module`, etc.
        signature: Signature instance.
        docstring: Docstring instance.
        members: Member objects. For example, methods of class.
        headless: Used in page mode.
        html: HTML after rendering.
    """

    obj: Any = field(default=None, repr=False)
    prefix: str = field(init=False)
    id: str = field(init=False)
    kind: str = field(init=False)
    signature: Signature = field(init=False)
    docstring: Docstring = field(init=False)
    sourcefile: str = field(init=False)
    lineno: int = field(init=False)
    members: List["Node"] = field(init=False)
    name_url: str = field(default="", init=False)
    prefix_url: str = field(default="", init=False)

    def __post_init__(self):
        obj = self.obj
        self.prefix, self.name = split_prefix_and_name(obj)
        self.id = self.name
        if self.prefix:
            self.id = ".".join([self.prefix, self.name])
        self.kind = get_kind(obj)
        self.signature = get_signature(obj)
        self.docstring = get_docstring(obj)
        self.sourcefile, self.lineno = get_sourcefile_and_lineno(obj)

        members = get_members(obj)
        if self.kind in ["class", "dataclass"] and not self.docstring:
            for member in members:
                if member.name == "__init__" and member.docstring:
                    markdown = member.docstring.sections[0].markdown
                    if not markdown.startswith("Initialize self"):
                        self.docstring = member.docstring
        self.members = [member for member in members if member.name != "__init__"]
        if self.docstring and self.docstring.type:
            self.type = self.docstring.type

    def __getitem__(self, index):
        return self.members[index]

    def __len__(self):
        return len(self.members)

    def __getattr__(self, name):
        for member in self.members:
            if member.name == name:
                return member

    def __iter__(self) -> Iterator[Base]:
        if self.docstring:
            yield from self.docstring
        for member in self.members:
            yield from member

    def get_markdown(self) -> str:
        """Returns a Markdown source for docstring of this object."""
        markdowns = []
        for base in self:
            markdown = mkapi.core.preprocess.convert(base.markdown)
            markdowns.append(markdown)
        return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)

    def set_html(self, html: str):
        """Sets HTML to `Base` instances recursively."""
        for base, html in zip(self, html.split("<!-- mkapi:sep -->")):
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
        else:
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
        member = Node(obj=obj)
        if member.docstring:
            members.append(member)
    return sorted(members, key=lambda x: (x.sourcefile, x.lineno))


@lru_cache(maxsize=1000)
def get_node(name: Any) -> Node:
    if isinstance(name, str):
        obj = get_object(name)
    else:
        obj = name

    return Node(obj=obj)
