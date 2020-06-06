from dataclasses import dataclass, field
from typing import Any, List

from mkapi.core.docstring import Docstring, get_docstring
from mkapi.core.object import get_sourcefile_and_lineno, split_prefix_and_name


@dataclass
class Tree:
    """Tree class. This class is the base of Node and Module.

    Attributes:
        obj: Object.
        prefix: Prefix.
        name: Name.
        id: ID for CSS.
        kind: Kind such as `function`, `class`, `module`, etc.
        docstring: Docstring instance.
        sourcefile: Source file path.
        lineno: int: Line number.
        members: Member objects. For example, methods of class.
        prefix_url: URL for prefix link.
        name_url: URL for name link.
    """

    obj: Any = field(repr=False)
    prefix: str = field(init=False)
    name: str = field(init=False)
    id: str = field(init=False)
    kind: str = field(init=False)
    docstring: Docstring = field(init=False)
    sourcefile: str = field(init=False)
    lineno: int = field(init=False)
    parent: Any = field(default=None, init=False)
    members: List[Any] = field(init=False)
    prefix_url: str = field(default="", init=False)
    name_url: str = field(default="", init=False)

    def __post_init__(self):
        obj = self.obj
        self.prefix, self.name = split_prefix_and_name(obj)
        self.id = self.name
        if self.prefix:
            self.id = ".".join([self.prefix, self.name])
        self.docstring = get_docstring(obj)
        self.sourcefile, self.lineno = get_sourcefile_and_lineno(obj)
        self.kind = self.get_kind()
        self.members = self.get_members()
        for member in self.members:
            member.parent = self

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.members[index]
        else:
            for member in self.members:
                if member.name == index:
                    return member

    def __getattr__(self, name):
        return self[name]

    def __len__(self):
        return len(self.members)

    def __contains__(self, name):
        for member in self.members:
            if member.name == name:
                return True
        return False

    def get_kind(self) -> str:
        """Returns kind of this object."""
        raise NotImplementedError

    def get_members(self) -> List["Tree"]:
        """Returns a list of members."""
        raise NotImplementedError

    def get_markdown(self) -> str:
        """Returns a Markdown source for docstring of this object."""
        raise NotImplementedError

    @property
    def markdown(self):
        if self.prefix:
            return f"[{self.prefix}]({self.prefix}).[{self.name}]({self.id})"
        else:
            return f"[{self.name}]({self.id})"
