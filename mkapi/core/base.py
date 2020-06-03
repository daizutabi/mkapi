"""This module provides entity classes to represent docstring structure."""
from dataclasses import dataclass, field
from typing import Any, Iterator, List, Optional

import mkapi.core.preprocess
from mkapi.core.inspect import Signature
from mkapi.core.renderer import renderer


@dataclass
class Base:
    """Base class.

    Args:
        name: Object name.
        type: Object type.
        markdown: Markdown source.

    Attributes:
        name: Object name.
        type: Object type.
        markdown: Markdown source.
        html: HTML after conversion.
    """

    name: str
    type: str = ""
    markdown: str = ""
    html: str = field(default="", init=False)

    def set_html(self, html: str):
        """Sets `html` attribute according to the givin `html` argument.

        In the simplest case, just store the argument to the attribute. But modify
        the attribute if necessary.
        """
        self.html = html


@dataclass
class Item(Base):
    """Item class represents an item in Parameters, Attributes, and Raises sections.

    Args:
        name: Object name.
        type: Object type.
        markdown: Markdown source.

    Attributes:
        name: Object name.
        type: Object type.
        markdown: Markdown source.
        html: HTML after conversion.
    """

    def set_html(self, html: str):
        """Sets `html` attribute according to the givin `html` argument.

        `p` tags are removed and `br` tags are inserted.
        """
        html = html.replace("<p>", "").replace("</p>", "<br>")
        if html.endswith("<br>"):
            html = html[:-4]
        self.html = html


@dataclass
class Section(Base):
    """Section class represents a section in docstring.

    Args:
        name: Object name.
        type: Object type.
        markdown: Markdown source.
        items: List for arguments, attributes, or exceptions.

    Attributes:
        name: Object name.
        type: Object type.
        markdown: Markdown source.
        items: List for arguments, attributes, or exceptions.
        html: HTML after conversion.
    """

    items: List[Item] = field(default_factory=list)

    def __iter__(self) -> Iterator[Base]:
        if self.markdown:
            yield self
        else:
            yield from self.items


@dataclass
class Docstring:
    """Docstring class represents a docstring of an object.

    Args:
        sections: List of Section instance
        type: Type for Returns and Yields sections.

    Attributes:
        sections: List of Section instance
        type: Type for Returns and Yields sections.
    """

    sections: List[Section]
    type: str = ""

    def __getitem__(self, name) -> Optional[Section]:
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def __iter__(self) -> Iterator[Base]:
        for section in self.sections:
            yield from section


@dataclass
class Node(Base):
    """Node class represents an object.

    Attributes:
        obj: Object.
        depth: Current depth of object searching.
        prefix: Prefix.
        kind: Kind such as `function`, `class`, `module`, etc.
        sourcefile: Souce filename thats defines this object.
        lineno: Line number.
        signature: Signature instance.
        docstring: Docstring instance.
        members: Member objects. For example, methods of class.
        headless: Used in page mode.
        html: HTML after rendering.
    """

    obj: Any = field(default=None, repr=False)
    depth: int = 0
    prefix: str = ""
    kind: str = ""
    sourcefile: str = ""
    lineno: int = 0
    signature: Optional[Signature] = None
    docstring: Optional[Docstring] = None
    members: List["Node"] = field(default_factory=list)
    headless: bool = False

    def __post_init__(self):
        if self.prefix:
            self.id = ".".join([self.prefix, self.name])
        else:
            self.id = self.name

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
