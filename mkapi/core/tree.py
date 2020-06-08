from dataclasses import dataclass, field
from typing import Any, List

from mkapi.core.base import Object
from mkapi.core.docstring import Docstring, get_docstring
from mkapi.core.object import get_sourcefile_and_lineno, split_prefix_and_name
from mkapi.core.signature import get_signature


@dataclass
class Tree:
    """Tree class. This class is the base of Node and Module.

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

    obj: Any = field(repr=False)
    sourcefile: str = field(init=False)
    lineno: int = field(init=False)
    object: Object = field(init=False)
    docstring: Docstring = field(init=False)
    parent: Any = field(default=None, init=False)
    members: List[Any] = field(init=False)

    def __post_init__(self):
        obj = self.obj
        self.sourcefile, self.lineno = get_sourcefile_and_lineno(obj)
        prefix, name = split_prefix_and_name(obj)
        kind = self.get_kind()
        signature = get_signature(obj)
        self.object = Object(prefix=prefix, name=name, kind=kind, signature=signature)
        self.docstring = get_docstring(obj)
        self.members = self.get_members()
        for member in self.members:
            member.parent = self

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.members[index]
        else:
            for member in self.members:
                if member.object.name == index:
                    return member

    def __getattr__(self, name):
        return self[name]

    def __len__(self):
        return len(self.members)

    def __contains__(self, name):
        for member in self.members:
            if member.object.name == name:
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
