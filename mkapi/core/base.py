"""This module provides entity classes to represent docstring structure."""
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from mkapi.core.preprocess import strip_ptags
from mkapi.core.regex import LINK_PATTERN


@dataclass
class Base:
    """Base class.

    Args:
        name: Object name.
        markdown: Markdown source.

    Attributes:
        name: Object name.
        markdown: Markdown source.
        html: HTML after conversion.
    """

    name: str = ""
    markdown: str = ""
    html: str = field(default="", init=False)

    def set_html(self, html: str):
        """Sets `html` attribute."""
        self.html = html


@dataclass
class Type(Base):
    """Type class represents type for other classes."""

    def __post_init__(self):
        if not self.markdown:
            self.markdown = self.name

    def __bool__(self):
        return self.name != ""

    def __iter__(self) -> Iterator[Base]:
        if LINK_PATTERN.search(self.markdown):
            yield self

    def set_html(self, html: str):
        """Sets `html` attribute cleaning `p` tags."""
        self.html = strip_ptags(html)


@dataclass
class Item(Base):
    """Item class represents an item in Parameters, Attributes, and Raises sections."""

    type: Type = field(default_factory=Type)

    def __iter__(self) -> Iterator[Base]:
        yield from self.type
        yield self

    def set_html(self, html: str):
        """Sets `html` attribute cleaning `p` tags."""
        self.html = strip_ptags(html)


@dataclass
class Section(Base):
    """Section class represents a section in docstring.

    Args:
        items: List for Arguments, Attributes, or Raises sections.

    Attributes:
        items: List for Arguments, Attributes, or Raises sections.

    Examples:
        `Section` is iterable:
        >>> section = Section('Returns', markdown='An integer.')
        >>> for x in section:
        ...     assert x is section

        >>> items = [Item('x'), Item('y'), Item('z')]
        >>> section = Section('Parameters', items=items)
        >>> [item.name for item in section]
        ['x', 'y', 'z']

        Indexing:
        >>> isinstance(section['y'], Item)
        True
        >>> section['z'].name
        'z'

        Contains:
        >>> 'x' in section
        True
    """

    items: List[Item] = field(default_factory=list)
    type: Type = field(default_factory=Type)

    def __iter__(self) -> Iterator[Base]:
        yield from self.type
        if self.markdown:
            yield self
        for item in self.items:
            yield from item

    def __getitem__(self, name) -> Optional[Item]:
        for item in self.items:
            if item.name == name:
                return item
        return None

    def __contains__(self, name) -> bool:
        return self[name] is not None


@dataclass
class Docstring:
    """Docstring class represents a docstring of an object.

    Args:
        sections: List of Section instance.
        type: Type for Returns and Yields sections.

    Attributes:
        sections: List of Section instance.
        type: Type for Returns and Yields sections.

    Examples:
        Empty docstring:
        >>> docstring = Docstring()
        >>> assert not docstring

        Docstring with 3 sections:
        >>> default = Section("", markdown="Default")
        >>> parameters = Section("Parameters", items=[Item("a"), Item("b")])
        >>> returns = Section("Returns", markdown="Results")
        >>> docstring = Docstring([default, parameters, returns])

        `Docstring` is iterable:
        >>> [base.name for base in docstring]
        ['', 'a', 'b', 'Returns']

        Indexing:
        >>> docstring["Parameters"].items[0].name
        'a'
    """

    sections: List[Section] = field(default_factory=list)
    type: Type = field(default_factory=Type)

    def __bool__(self):
        return len(self.sections) > 0

    def __iter__(self) -> Iterator[Base]:
        yield from self.type
        for section in self.sections:
            yield from section

    def __getitem__(self, name: str) -> Optional[Section]:
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def __setitem__(self, name: str, section: Section):
        for k, section_ in enumerate(self.sections):
            if section_.name == name:
                self.sections[k] = section
                return
            if name == "Parameters" and section_.name != "":
                self.sections.insert(k, section)
                return
            if section_.name in ["Raises", "Yields", "Returns"]:
                self.sections.insert(k, section)
                return
        self.sections.append(section)
