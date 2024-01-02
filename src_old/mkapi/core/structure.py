"""Base class of [Node](mkapi.nodes.Node) and [Module](mkapi.modules.Module)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

from mkapi.docstring import Base, Docstring, Type, parse_docstring

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class Object(Base):
    """Object class represents an object.

    Args:
        name: Object name.
        prefix: Object prefix.
        qualname: Qualified name.
        kind: Object kind such as 'class', 'function', *etc.*
        signature: Signature if object is module or callable.

    Attributes:
        id: ID attribute of HTML.
        type: Type for missing Returns and Yields sections.
    """

    prefix: str = ""
    qualname: str = ""
    kind: str = ""
    signature: Signature = field(default_factory=Signature)
    module: str = field(init=False)
    markdown: str = field(init=False)
    id: str = field(init=False)  # noqa: A003
    type: Type = field(default_factory=Type, init=False)  # noqa: A003

    def __post_init__(self) -> None:
        from mkapi.core import link

        self.id = self.name
        if self.prefix:
            self.id = f"{self.prefix}.{self.name}"
        if not self.qualname:
            self.module = self.id
        else:
            self.module = self.id[: -len(self.qualname) - 1]
        if not self.markdown:
            name = link.link(self.name, self.id)
            if self.prefix:
                prefix = link.link(self.prefix, self.prefix)
                self.markdown = f"{prefix}.{name}"
            else:
                self.markdown = name

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self.id!r})"

    def __iter__(self) -> Iterator[Base]:
        yield from self.type
        yield self


@dataclass
class Tree:
    """Base of [Node](mkapi.core.node.Node) and [Module](mkapi.core.module.Module).

    Args:
        obj: Object.

    Attributes:
        sourcefile: Source file path.
        lineno: Line number.
        object: Object instance.
        docstring: Docstring instance.
        parent: Parent instance.
        members: Member instances.
    """

    obj: Any = field()
    sourcefile: str = field(init=False)
    lineno: int = field(init=False)
    object: Object = field(init=False)  # noqa: A003
    docstring: Docstring = field(init=False)
    parent: Any = field(default=None, init=False)
    members: list[Self] = field(init=False)

    def __post_init__(self) -> None:
        obj = get_origin(self.obj)
        self.sourcefile, self.lineno = get_sourcefile_and_lineno(obj)
        prefix, name = split_prefix_and_name(obj)
        qualname = get_qualname(obj)
        kind = self.get_kind()
        signature = get_signature(obj)
        self.object = Object(
            prefix=prefix,
            name=name,
            qualname=qualname,
            kind=kind,
            signature=signature,
        )
        self.docstring = get_docstring(obj)
        self.obj = obj
        self.members = self.get_members()
        for member in self.members:
            member.parent = self

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        id_ = self.object.id
        sections = len(self.docstring.sections)
        numbers = len(self.members)
        return f"{class_name}({id_!r}, num_sections={sections}, num_members={numbers})"

    def __getitem__(self, index: int | str | list[str]) -> Self:
        """Return a member {class} instance.

        If `index` is str, a member Tree instance whose name is equal to `index`
        is returned.

        Raises:
            IndexError: If no member found.
        """
        if isinstance(index, list):
            node = self
            for name in index:
                node = node[name]
            return node
        if isinstance(index, int):
            return self.members[index]
        if isinstance(index, str) and "." in index:
            names = index.split(".")
            return self[names]
        for member in self.members:
            if member.object.name == index:
                return member
        raise IndexError

    def __len__(self) -> int:
        return len(self.members)

    def __contains__(self, name: str) -> bool:
        return any(member.object.name == name for member in self.members)

    def get_kind(self) -> str:
        """Returns kind of self."""
        raise NotImplementedError

    def get_members(self) -> list[Self]:
        """Returns a list of members."""
        raise NotImplementedError

    def get_markdown(self) -> str:
        """Returns a Markdown source for docstring of self."""
        raise NotImplementedError

    def walk(self) -> Iterator[Self]:
        """Yields all members."""
        yield self
        for member in self.members:
            yield from member.walk()
