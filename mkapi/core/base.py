"""This module provides entity classes to represent docstring structure."""
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from mkapi.core import preprocess
from mkapi.core import linker
from mkapi.core.regex import LINK_PATTERN
from mkapi.core.signature import Signature


@dataclass
class Base:
    """Base class.

    Args:
        name: Object name.
        markdown: Markdown source.

    Attributes:
        html: HTML after conversion.
    """

    name: str = ""
    markdown: str = ""
    html: str = field(default="", init=False)

    def set_html(self, html: str):
        """Sets `html` attribute.

        Args:
            html: HTML string.
        """
        self.html = html


@dataclass
class Type(Base):
    """Type class represents type for [Item](), [Section](), [Docstring](),
    and [Object]()."""

    def __post_init__(self):
        if not self.markdown:
            self.markdown = self.name

    def __bool__(self) -> bool:
        """Returns True if name is not empty."""
        return self.name != ""

    def __iter__(self) -> Iterator[Base]:
        """Yields self if the markdown attribute has link form."""
        if LINK_PATTERN.search(self.markdown):
            yield self

    def set_html(self, html: str):
        """Sets `html` attribute cleaning `p` tags."""
        self.html = preprocess.strip_ptags(html)


@dataclass
class Item(Base):
    """Item class represents an item in Parameters, Attributes, and Raises sections.

    Args:
        type: Type of self.
        kind: Kind of item, for example `readonly_property`. This value is rendered
            to CSS class attribute.

    Attributes:
        type: Type of self.
        kind: Kind of item, for example `readonly_property`. This value is rendered
            to CSS class attribute.
    """

    type: Type = field(default_factory=Type)
    kind: str = ""

    def __iter__(self) -> Iterator[Base]:
        yield from self.type
        yield self

    def set_html(self, html: str):
        """Sets `html` attribute cleaning `p` tags."""
        self.html = preprocess.strip_ptags(html)


@dataclass
class Section(Base):
    """Section class represents a section in docstring.

    Args:
        items: List for Arguments, Attributes, or Raises sections.
        type: Type of self.

    Attributes:
        items: List for Arguments, Attributes, or Raises sections.
        type: Type of self.

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

    def __post_init__(self):
        if self.markdown:
            self.markdown = preprocess.convert(self.markdown)

    def __iter__(self) -> Iterator[Base]:
        """Yields [Base]() instance that has non empty Markdown.

        Args:
            name: Item name.
        """
        yield from self.type
        if self.markdown:
            yield self
        for item in self.items:
            yield from item

    def __getitem__(self, name) -> Optional[Item]:
        """Returns [Item]() instance whose name is equal to `name`. If not found,
        returns None.

        Args:
            name: Item name.
        """
        for item in self.items:
            if item.name == name:
                return item
        return None

    def __delitem__(self, name):
        """Delete [Item]() instance whose name is equal to `name`.

        Args:
            name: Item name.
        """
        for k, item in enumerate(self.items):
            if item.name == name:
                del self.items[k]

    def __contains__(self, name) -> bool:
        """Returns True if there is [Item]() instance whose name is `name`.

        Args:
            name: Item name.
        """
        return self[name] is not None


@dataclass
class Docstring:
    """Docstring class represents a docstring of an object.

    Args:
        sections: List of Section instance.
        type: Type for Returns or Yields sections.

    Attributes:
        sections: List of Section instance.
        type: Type for missing Returns or Yields sections.

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
        if name == 'Methods':
            self.sections.append(section)
            return
        for k, section_ in enumerate(self.sections):
            if section_.name == name:
                self.sections[k] = section
                return
            if name == "Bases":
                self.sections.insert(k, section)
                return
            if name == "Parameters" and section_.name not in ["", "Bases"]:
                self.sections.insert(k, section)
                return
            if section_.name in ["Raises", "Yields", "Returns"]:
                self.sections.insert(k, section)
                return
        self.sections.append(section)


@dataclass
class Object(Base):
    """Object class represents an object.

    Args:
        name: Object name. `Item` for `Item` class.
        prefix: Object prefix. `mkapi.core.base` for `Item` class.
        kind: Object kind such as 'class', 'function'. etc.
        type: Type for missing Returns and Yields sections.
        signature: Signature if object is module or callable.

    Attributes:
        id: CSS ID.
    """

    prefix: str = ""
    qualname: str = ""
    id: str = field(init=False)
    kind: str = ""
    type: Type = field(default_factory=Type)
    signature: Signature = field(default_factory=Signature)

    def __post_init__(self):
        self.id = self.name
        if self.prefix:
            self.id = ".".join([self.prefix, self.name])
        if not self.markdown:
            name = linker.link(self.name, self.id)
            if self.prefix:
                prefix = linker.link(self.prefix, self.prefix)
                self.markdown = ".".join([prefix, name])
            else:
                self.markdown = name

    def __iter__(self) -> Iterator[Base]:
        yield from self.type
        yield self
