"""This modules provides Node class that has tree structure."""
import inspect
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterator, List, Optional

from mkapi.core.base import Base, Object
from mkapi.core.object import from_object, get_object, get_sourcefiles
from mkapi.core.tree import Tree


@dataclass
class Node(Tree):
    """Node class represents an object.

    Args:
        sourcefile_index: If `obj` is a member of class, this value is the index of
            unique source files given by `mro()` of the class. Otherwise, 0.

    Attributes:
        parent: Parent Node instance.
        members: Member Node instances.
    """

    parent: Optional["Node"] = field(default=None, init=False)
    members: List["Node"] = field(init=False)
    sourcefile_index: int = 0

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
        if inspect.isclass(self.obj):
            ms = [m.object for m in self.members if m.object.kind == "method"]
        if self.docstring and self.docstring.type:
            self.object.type = self.docstring.type

    def __iter__(self) -> Iterator[Base]:
        yield self.object
        yield from self.docstring
        for member in self.members:
            yield from member

    def get_kind(self) -> str:
        if inspect.ismodule(self.obj):
            if self.sourcefile.endswith("__init__.py"):
                return "package"
            else:
                return "module"
        return get_kind(self.obj)

    def get_members(self) -> List["Node"]:  # type:ignore
        return get_members(self.obj)

    def get_markdown(self, level: int = 0, callback=None) -> str:
        """Returns a Markdown source for docstring of this object.

        Args:
            level: Heading level. If 0, `<div>` tags are used.
            callback (callable, optional): To modify Markdown source.
        """
        markdowns = []
        for base in self:
            if callback:
                markdown = callback(base)
            else:
                markdown = base.markdown
            if isinstance(base, Object):
                if level and self.parent is None:
                    markdown = "#" * level + " " + markdown
            markdowns.append(markdown)
        return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)

    def set_html(self, html: str):
        """Sets HTML to [Base]() instances recursively.

        Args:
            html: HTML that is provided by a Markdown converter.
        """
        for base, html in zip(self, html.split("<!-- mkapi:sep -->")):
            base.set_html(html.strip())

    def render(self) -> str:
        """Renders and returns HTML."""
        from mkapi.core.renderer import renderer

        return renderer.render(self)  # type:ignore


def get_kind(obj) -> str:
    if isinstance(obj, property):
        if obj.fset:
            return "readwrite_property"
        else:
            return "readonly_property"
    if hasattr(obj, "__dataclass_fields__") and hasattr(obj, "__qualname__"):
        return "dataclass"
    if hasattr(obj, "__self__") and type(obj.__self__) is type:
        return "classmethod"
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
        if hasattr(obj, "__qualname__") and "." in obj.__qualname__:
            return "staticmethod"
        return "function"
    return ""


def is_member(name: str, obj: Any, sourcefiles: List[str]) -> int:
    """Returns an integer thats indicates if `obj` is a member or not.

    * $-1$ : Is not a member.
    * $>0$ : Is a member. If the value is larger than 0, `obj` is defined
        in different file and the value is corresponding to the index of unique
        source files of superclasses.

    Args:
        name: Object name.
        obj: Object
        sourcefiles: Parent source files. If the parent is a class,
            those of the superclasses should be included in the order
            of `mro()`.
    """
    if isinstance(obj, property):
        obj = obj.fget
    if name in ["__func__", "__self__"]:
        return -1
    if name.startswith("_"):
        if not name.startswith("__") or not name.endswith("__"):
            return -1
    if not get_kind(obj):
        return -1
    try:
        sourcefile = inspect.getsourcefile(obj)
    except TypeError:
        return -1
    if not sourcefiles:
        return 0
    for sourcefile_index, parent_sourcefile in enumerate(sourcefiles):
        if sourcefile == parent_sourcefile:
            if inspect.isclass(obj):
                try:
                    obj.mro()
                except (TypeError, AttributeError):
                    return -1
            return sourcefile_index
    return -1


def get_members(obj: Any) -> List[Node]:
    if inspect.ismodule(obj) or isinstance(obj, property):
        return []

    sourcefiles = get_sourcefiles(obj)
    members = []
    for name, obj in inspect.getmembers(obj):
        sourcefile_index = is_member(name, obj, sourcefiles)
        if sourcefile_index != -1 and not from_object(obj):
            member = get_node(obj, sourcefile_index)
            if member.docstring:
                members.append(member)
    return sorted(members, key=lambda x: (-x.sourcefile_index, x.lineno))


USE_CACHE = True


@lru_cache(maxsize=1000)
def _get_node(obj, sourcefile_index) -> Node:
    return Node(obj, sourcefile_index)


def get_node(name, sourcefile_index: int = 0) -> Node:
    """Returns a Node instace by name or object.

    Args:
        name: Object name or object itself.
        sourcefile_index: If `obj` is a member of class, this value is the index of
            unique source files given by `mro()` of the class. Otherwise, 0.
    """
    if isinstance(name, str):
        obj = get_object(name)
    else:
        obj = name

    if USE_CACHE:
        return _get_node(obj, sourcefile_index)
    else:
        return Node(obj, sourcefile_index)
