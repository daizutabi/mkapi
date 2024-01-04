"""Node class that has tree structure."""
import inspect
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from types import FunctionType
from typing import Optional

from mkapi.core import preprocess
from mkapi.core.base import Base, Type
from mkapi.core.object import from_object, get_object, get_origin, get_sourcefiles
from mkapi.core.structure import Object, Tree
from mkapi.inspect.attribute import isdataclass


@dataclass(repr=False)
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
    members: list["Node"] = field(init=False)
    sourcefile_index: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.object.kind in ["class", "dataclass"] and not self.docstring:
            for member in self.members:
                if member.object.name == "__init__" and member.docstring:
                    markdown = member.docstring.sections[0].markdown
                    if not markdown.startswith("Initialize self"):
                        self.docstring = member.docstring
        self.members = [m for m in self.members if m.object.name != "__init__"]

        doc = self.docstring
        if doc and "property" in self.object.kind:  # noqa: SIM102
            if not doc.type and len(doc.sections) == 1 and doc.sections[0].name == "":
                section = doc.sections[0]
                markdown = section.markdown
                type_, markdown = preprocess.split_type(markdown)
                if type_:
                    doc.type = Type(type_)
                    section.markdown = markdown

        if doc and doc.type:
            self.object.type = doc.type
            doc.type = Type()

    def __iter__(self) -> Iterator[Base]:
        yield from self.object
        yield from self.docstring
        for member in self.members:
            yield from member

    def get_kind(self) -> str:
        """Return node kind."""
        if inspect.ismodule(self.obj):
            if self.sourcefile.endswith("__init__.py"):
                return "package"
            return "module"
        if isinstance(self.obj, property):
            kind = "readwrite property" if self.obj.fset else "readonly property"
        else:
            kind = get_kind(get_origin(self.obj))
        if is_abstract(self.obj):
            return "abstract " + kind
        return kind

    def get_members(self) -> list["Node"]:
        """Return members."""
        return get_members(self.obj)

    def get_markdown(
        self,
        level: int = 0,
        callback: Callable[[Base], str] | None = None,
    ) -> str:
        """Return a Markdown source for docstring of this object.

        Args:
            level: Heading level. If 0, `<div>` tags are used.
            callback: To modify Markdown source.
        """
        markdowns = []
        member_objects = [member.object for member in self.members]
        class_name = ""
        for base in self:
            markdown = callback(base) if callback else base.markdown
            markdown = markdown.replace("{class}", class_name)
            if isinstance(base, Object):
                if level:
                    if base == self.object:
                        markdown = "#" * level + " " + markdown
                    elif base in member_objects:
                        markdown = "#" * (level + 1) + " " + markdown
                if "class" in base.kind:
                    class_name = base.name
            markdowns.append(markdown)
        return "\n\n<!-- mkapi:sep -->\n\n".join(markdowns)

    def set_html(self, html: str) -> None:
        """Set HTML to [Base]() instances recursively.

        Args:
            html: HTML that is provided by a Markdown converter.
        """
        for base, html_ in zip(self, html.split("<!-- mkapi:sep -->"), strict=False):
            base.set_html(html_.strip())

    def get_html(self, filters: list[str] | None = None) -> str:
        """Render and return HTML."""
        from mkapi.core.renderer import renderer

        return renderer.render(self, filters)


def is_abstract(obj: object) -> bool:
    """Return true if `obj` is abstract."""
    if inspect.isabstract(obj):
        return True
    if hasattr(obj, "__isabstractmethod__") and obj.__isabstractmethod__:  # type: ignore
        return True
    return False


def has_self(obj: object) -> bool:
    """Return true if `obj` has `__self__`."""
    try:
        return hasattr(obj, "__self__")
    except KeyError:
        return False


def get_kind_self(obj: object) -> str:  # noqa: D103
    try:
        self = obj.__self__  # type: ignore
    except KeyError:
        return ""
    if isinstance(self, type) or type(type(self)):  # Issue#18
        return "classmethod"
    return ""


def get_kind_function(obj: FunctionType) -> str:  # noqa: D103
    try:
        parameters = inspect.signature(obj).parameters
    except (ValueError, TypeError):
        return ""
    if parameters and next(iter(parameters)) == "self":
        return "method"
    if hasattr(obj, "__qualname__") and "." in obj.__qualname__:
        return "staticmethod"
    return "function"


KIND_FUNCTIONS: list[tuple[Callable[..., bool], str | Callable[..., str]]] = [
    (isdataclass, "dataclass"),
    (inspect.isclass, "class"),
    (inspect.isgeneratorfunction, "generator"),
    (has_self, get_kind_self),
    (inspect.isfunction, get_kind_function),
]


def get_kind(obj: object) -> str:
    """Return kind of object."""
    for func, kind in KIND_FUNCTIONS:
        if func(obj) and (kind_ := kind if isinstance(kind, str) else kind(obj)):
            return kind_
    return ""


def is_member(obj: object, name: str = "", sourcefiles: list[str] | None = None) -> int:  # noqa: PLR0911
    """Return an integer thats indicates if `obj` is a member or not.

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
    name = name or obj.__name__
    obj = get_origin(obj)
    if name in ["__func__", "__self__", "__base__", "__bases__"]:
        return -1
    if name.startswith("_"):  # noqa: SIM102
        if not name.startswith("__") or not name.endswith("__"):
            return -1
    if not get_kind(obj):
        return -1
    try:
        sourcefile = inspect.getsourcefile(obj)  # type: ignore
    except TypeError:
        return -1
    if not sourcefile:
        return -1
    if not sourcefiles:
        return 0
    sourcefile_path = Path(sourcefile)
    for sourcefile_index, parent_sourcefile in enumerate(sourcefiles):
        if Path(parent_sourcefile) == sourcefile_path:
            return sourcefile_index
    return -1


def get_members(obj: object) -> list[Node]:
    """Return members."""
    sourcefiles = get_sourcefiles(obj)
    members = []
    for name, obj_ in inspect.getmembers(obj):
        sourcefile_index = is_member(obj_, name, sourcefiles)
        if sourcefile_index != -1 and not from_object(obj_):
            member = get_node(obj_, sourcefile_index)
            if member.docstring:
                members.append(member)
    return sorted(members, key=lambda x: (-x.sourcefile_index, x.lineno))


def get_node(name: str | object, sourcefile_index: int = 0) -> Node:
    """Return a Node instace by name or object.

    Args:
        name: Object name or object itself.
        sourcefile_index: If `obj` is a member of class, this value is the index of
            unique source files given by `mro()` of the class. Otherwise, 0.
    """
    obj = get_object(name) if isinstance(name, str) else name
    return Node(obj, sourcefile_index)


def get_node_from_module(name: str | object) -> None:
    """Return a Node instace by name or object from `modules` dict."""
    from mkapi.core.module import modules

    obj = get_object(name) if isinstance(name, str) else name
    return modules[obj.__module__].node[obj.__qualname__]  # type: ignore
