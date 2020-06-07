import inspect
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterator, List

import mkapi.core.preprocess
from mkapi.core.base import Base
from mkapi.core.object import get_object
from mkapi.core.renderer import renderer
from mkapi.core.tree import Tree


@dataclass
class Node(Tree):
    """Node class represents an object.

    Attributes:
        obj: Object.
        signature: Signature instance.
        object: Object instance.
        docstring: Docstring instance.
        members: Member objects. For example, methods of class.
        html: HTML after rendering.
    """

    members: List["Node"] = field(init=False)

    def __post_init__(self):
        super().__post_init__()

        members = self.members
        if self.object.kind in ["class", "dataclass"] and not self.docstring:
            for member in members:
                if member.object.name == "__init__" and member.docstring:
                    markdown = member.docstring.sections[0].markdown
                    if not markdown.startswith("Initialize self"):
                        self.docstring = member.docstring
        self.members = [m for m in members if m.object.name != "__init__"]
        if self.docstring and self.docstring.type:
            self.object.type = self.docstring.type

    def __iter__(self) -> Iterator[Base]:
        yield self.object
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
                print(html.strip())
                self.html = html  # FIXME
            else:
                base.set_html(html.strip())

    def render(self) -> str:
        return renderer.render(self)


def get_kind(obj) -> str:
    if isinstance(obj, property):
        if obj.fset:
            return "readwrite_property"
        else:
            return "readonly_property"
    if hasattr(obj, "__dataclass_fields__") and hasattr(obj, "__qualname__"):
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


def is_member(name: str, obj: Any, sourcefile: str) -> bool:
    if isinstance(obj, property):
        return True
    if name.startswith("_") and name != "__init__":
        return False
    if not get_kind(obj):
        return False
    try:
        source = inspect.getsourcefile(obj)
    except TypeError:
        return False
    if sourcefile and source != sourcefile:
        return False
    return True


def get_members(obj) -> List[Node]:
    if inspect.ismodule(obj) or isinstance(obj, property):
        return []

    try:
        sourcefile = inspect.getsourcefile(obj) or ""
    except TypeError:
        sourcefile = ""
    members = []
    for name, obj in inspect.getmembers(obj):
        if is_member(name, obj, sourcefile):
            member = get_node(obj)
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
