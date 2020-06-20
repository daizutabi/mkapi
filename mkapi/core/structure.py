"""This module provides base class of [Node](mkapi.core.node.Node) and
[Module](mkapi.core.module.Module)."""
from dataclasses import dataclass, field
from typing import Any, Iterator, List, Union

from mkapi.core.base import Base, Type
from mkapi.core.docstring import Docstring, get_docstring
from mkapi.core.object import (get_origin, get_qualname,
                               get_sourcefile_and_lineno,
                               split_prefix_and_name)
from mkapi.core.signature import Signature, get_signature

"a.b.c".rpartition(".")


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
    id: str = field(init=False)
    type: Type = field(default_factory=Type, init=False)

    def __post_init__(self):
        from mkapi.core import linker

        self.id = self.name
        if self.prefix:
            self.id = ".".join([self.prefix, self.name])
        if not self.qualname:
            self.module = self.id
        else:
            self.module = self.id[: -len(self.qualname) - 1]
        if not self.markdown:
            name = linker.link(self.name, self.id)
            if self.prefix:
                prefix = linker.link(self.prefix, self.prefix)
                self.markdown = ".".join([prefix, name])
            else:
                self.markdown = name

    def __repr__(self):
        class_name = self.__class__.__name__
        id = self.id
        return f"{class_name}({id!r})"

    def __iter__(self) -> Iterator[Base]:
        yield from self.type
        yield self


@dataclass
class Tree:
    """Tree class. This class is the base class of [Node](mkapi.core.node.Node)
    and [Module](mkapi.core.module.Module).

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
    object: Object = field(init=False)
    docstring: Docstring = field(init=False)
    parent: Any = field(default=None, init=False)
    members: List[Any] = field(init=False)

    def __post_init__(self):
        obj = get_origin(self.obj)
        self.sourcefile, self.lineno = get_sourcefile_and_lineno(obj)
        prefix, name = split_prefix_and_name(obj)
        qualname = get_qualname(obj)
        kind = self.get_kind()
        signature = get_signature(obj)
        self.object = Object(
            prefix=prefix, name=name, qualname=qualname, kind=kind, signature=signature,
        )
        self.docstring = get_docstring(obj)
        self.obj = obj
        self.members = self.get_members()
        for member in self.members:
            member.parent = self

    def __repr__(self):
        class_name = self.__class__.__name__
        id = self.object.id
        sections = len(self.docstring.sections)
        numbers = len(self.members)
        return f"{class_name}({id!r}, num_sections={sections}, num_members={numbers})"

    def __getitem__(self, index: Union[int, str, List[str]]):
        """Returns a member {class} instance.

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

    def __len__(self):
        return len(self.members)

    def __contains__(self, name):
        for member in self.members:
            if member.object.name == name:
                return True
        return False

    def get_kind(self) -> str:
        """Returns kind of self."""
        raise NotImplementedError

    def get_members(self) -> List["Tree"]:
        """Returns a list of members."""
        raise NotImplementedError

    def get_markdown(self) -> str:
        """Returns a Markdown source for docstring of self."""
        raise NotImplementedError

    def walk(self):
        """Yields all members."""
        yield self
        for member in self.members:
            yield from member.walk()
